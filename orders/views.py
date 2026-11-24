import json
import logging
import re
import smtplib
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import urllib.error

from django.conf import settings
from django.core.mail import BadHeaderError
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .models import BuilderSize, BuilderTopping, MenuCollection, Order, Product, SiteSettings

logger = logging.getLogger(__name__)
ORDER_NOTIFICATION_EMAIL = "aevlyovva@gmail.com"
MAX_ORDER_ITEMS = 30
MAX_ITEM_QUANTITY = 50
MAX_ORDER_QUANTITY = 100
MAX_ORDER_TOTAL = Decimal("999999.99")
LARGE_BASE_PRICE = Decimal("1.50")


def build_order_message(order):
    if order.order_type == order.DELIVERY:
        receiving = f"Доставка до: {order.delivery_address or '-'}"
    else:
        receiving = f"Лично взимане: {order.pickup_location or '-'}"

    item_lines = []
    for item in order.items:
        name = item.get("name", "Продукт")
        quantity = item.get("quantity", 1)
        price = item.get("price", "")
        item_lines.append(f"- {name} × {quantity} ({price} €)")

    return "\n".join([
        f"Получена е нова поръчка #{order.id}.",
        "",
        f"Клиент: {order.customer_name or '-'}",
        f"Телефон: {order.customer_phone or '-'}",
        receiving,
        "",
        "Продукти:",
        *item_lines,
        "",
        f"Обща сума: {order.total} €",
    ])


def send_order_notification(order):
    recipient = ORDER_NOTIFICATION_EMAIL

    subject = f"Нова поръчка #{order.id}"
    message = build_order_message(order)

    try:
        return send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        ) == 1
    except (BadHeaderError, OSError, smtplib.SMTPException):
        logger.exception("Failed to send notification email for order #%s", order.id)
        return False


def normalize_whatsapp_phone(phone):
    digits = "".join(character for character in (phone or "") if character.isdigit())
    if not digits:
        return ""
    if digits.startswith("00"):
        return digits[2:]
    if digits.startswith("0"):
        return f"359{digits[1:]}"
    return digits


def send_whatsapp_notification(order):
    site = SiteSettings.objects.first()
    recipient = normalize_whatsapp_phone(
        site.order_notification_phone if site else ""
    )
    if not recipient:
        return False

    message = build_order_message(order)
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
    access_token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")

    if phone_number_id and access_token:
        try:
            payload = json.dumps({
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"body": message},
            }).encode("utf-8")
            request = Request(
                f"https://graph.facebook.com/v22.0/{phone_number_id}/messages",
                data=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urlopen(request, timeout=10) as response:
                return 200 <= response.status < 300
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            logger.exception("Failed to send WhatsApp notification for order #%s", order.id)

    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    twilio_from = getattr(settings, "TWILIO_WHATSAPP_FROM", "")
    if account_sid and auth_token and twilio_from:
        try:
            import base64

            data = urlencode({
                "From": twilio_from,
                "To": f"whatsapp:+{recipient}",
                "Body": message,
            }).encode("utf-8")
            credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")
            request = Request(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                data=data,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
            )
            with urlopen(request, timeout=10) as response:
                return 200 <= response.status < 300
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            logger.exception("Failed to send Twilio WhatsApp notification for order #%s", order.id)

    return False


def home(request):
    products = Product.objects.filter(
        is_available=True,
        collection__is_active=True,
    ).select_related("collection")
    collections = MenuCollection.objects.filter(is_active=True).prefetch_related("products")
    settings_obj, _ = SiteSettings.objects.get_or_create(pk=1)
    return render(request, "index.html", {
        "products": products,
        "site": settings_obj,
        "builder_sizes": BuilderSize.objects.filter(is_active=True),
        "builder_toppings": BuilderTopping.objects.filter(is_active=True),
        "collections": collections,
    })


def parse_positive_int(value):
    if isinstance(value, bool):
        raise ValueError
    parsed = int(value)
    if parsed <= 0 or str(parsed) != str(value):
        raise ValueError
    return parsed


def build_order_items(raw_items):
    if not isinstance(raw_items, list) or not raw_items or len(raw_items) > MAX_ORDER_ITEMS:
        raise ValueError("Невалидни продукти в поръчката.")

    normalized_items = []
    total = Decimal("0.00")
    total_quantity = 0

    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise ValueError("Невалидни продукти в поръчката.")
        quantity = parse_positive_int(raw_item.get("quantity"))
        if quantity > MAX_ITEM_QUANTITY:
            raise ValueError("Количеството на продукт е прекалено голямо.")
        total_quantity += quantity
        if total_quantity > MAX_ORDER_QUANTITY:
            raise ValueError("Общото количество в поръчката е прекалено голямо.")

        item_type = raw_item.get("type")
        if item_type == "product":
            product_id = parse_positive_int(raw_item.get("productId"))
            product = Product.objects.filter(
                pk=product_id,
                is_available=True,
                collection__is_active=True,
            ).first()
            if product is None or product.price is None or product.price <= 0:
                raise ValueError("Един от избраните продукти вече не е наличен.")
            name = product.name
            price = product.price
        elif item_type == "builder":
            size_id = parse_positive_int(raw_item.get("sizeId"))
            size = BuilderSize.objects.filter(pk=size_id, is_active=True).first()
            base_type = raw_item.get("base")
            topping_ids = raw_item.get("toppingIds")
            if size is None or size.price <= 0 or base_type not in ("classic", "large"):
                raise ValueError("Невалиден избор за персонализиран картоф.")
            if (
                not isinstance(topping_ids, list)
                or len(topping_ids) > 20
                or len(topping_ids) != size.topping_count
                or len(set(topping_ids)) != len(topping_ids)
            ):
                raise ValueError("Изберете точния брой различни добавки за картофа.")
            parsed_topping_ids = [parse_positive_int(value) for value in topping_ids]
            toppings = list(
                BuilderTopping.objects.filter(
                    pk__in=parsed_topping_ids,
                    is_active=True,
                ).order_by("sort_order", "name")
            )
            if len(toppings) != size.topping_count:
                raise ValueError("Една или повече избрани добавки вече не са налични.")
            if any(topping.extra_price < 0 for topping in toppings):
                raise ValueError("Цената на една или повече добавки е невалидна.")
            base_name = "класически печен картоф" if base_type == "classic" else "голям печен картоф"
            price = size.price + (LARGE_BASE_PRICE if base_type == "large" else Decimal("0.00"))
            price += sum((topping.extra_price for topping in toppings), Decimal("0.00"))
            name = f"Картоф по избор — {size.name}, {base_name}; добавки: {', '.join(topping.name for topping in toppings)}"
        else:
            raise ValueError("Невалиден тип продукт.")

        line_total = price * quantity
        total += line_total
        if total > MAX_ORDER_TOTAL:
            raise ValueError("Общата сума на поръчката е прекалено голяма.")
        normalized_items.append({
            "name": name,
            "price": str(price.quantize(Decimal("0.01"))),
            "quantity": quantity,
        })

    return normalized_items, total.quantize(Decimal("0.01"))


@require_POST
def create_order(request):
    if len(request.body) > 65536:
        return JsonResponse({"error": "Заявката е прекалено голяма."}, status=413)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Невалидни данни."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Невалидни данни."}, status=400)
    order_type = data.get("orderType")
    if order_type not in (Order.DELIVERY, Order.PICKUP):
        return JsonResponse({"error": "Невалидна поръчка."}, status=400)

    phone_value = data.get("customerPhone", "")
    if not isinstance(phone_value, str):
        return JsonResponse({"error": "Въведете телефонен номер с точно 10 цифри, започващ с 0."}, status=400)
    customer_phone = re.sub(r"[^0-9]", "", phone_value)
    if not re.fullmatch(r"0[0-9]{9}", customer_phone):
        return JsonResponse({"error": "Въведете телефонен номер с точно 10 цифри, започващ с 0."}, status=400)

    customer_name = data.get("customerName")
    if not isinstance(customer_name, str) or not customer_name.strip() or len(customer_name.strip()) > 120:
        return JsonResponse({"error": "Въведете име (до 120 символа)."}, status=400)
    customer_name = customer_name.strip()

    site, _ = SiteSettings.objects.get_or_create(pk=1)
    if order_type == Order.DELIVERY:
        address = data.get("address")
        if not isinstance(address, str) or not address.strip() or len(address.strip()) > 255:
            return JsonResponse({"error": "Въведете адрес за доставка."}, status=400)
        delivery_address = address.strip()
        pickup_location = ""
    else:
        pickup_location = data.get("pickupLocation")
        valid_locations = {
            location.strip()
            for location in (
                site.address if site else "",
                site.second_address if site else "",
            )
            if location and location.strip()
        }
        if not isinstance(pickup_location, str) or pickup_location not in valid_locations:
            return JsonResponse({"error": "Изберете валиден обект за взимане."}, status=400)
        delivery_address = ""

    raw_items = data.get("items")
    if not isinstance(raw_items, list):
        return JsonResponse({"error": "Невалидни продукти в поръчката."}, status=400)
    try:
        items, total = build_order_items(raw_items)
    except (InvalidOperation, TypeError, ValueError, OverflowError):
        return JsonResponse({"error": "Невалидни продукти или количества в поръчката."}, status=400)

    order = Order.objects.create(
        order_type=order_type,
        customer_name=customer_name,
        customer_phone=customer_phone,
        delivery_address=delivery_address,
        pickup_location=pickup_location,
        items=items,
        total=total,
    )
    email_sent = send_order_notification(order)
    whatsapp_sent = send_whatsapp_notification(order)
    return JsonResponse({
        "success": True,
        "orderId": order.id,
        "emailSent": email_sent,
        "whatsappSent": whatsapp_sent,
        "notificationSent": email_sent or whatsapp_sent,
    })
