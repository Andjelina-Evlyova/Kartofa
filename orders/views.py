import json
import logging
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import urllib.error

from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .models import BuilderSize, BuilderTopping, MenuCollection, Order, Product, SiteSettings

logger = logging.getLogger(__name__)


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
    site = SiteSettings.objects.first()
    recipient = site.order_notification_email.strip() if site and site.order_notification_email else ""
    if not recipient:
        return False

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
    except Exception:
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
    products = Product.objects.filter(is_available=True)
    collections = MenuCollection.objects.filter(is_active=True).prefetch_related("products")
    settings_obj = SiteSettings.objects.first()
    if settings_obj is None:
        settings_obj = SiteSettings.objects.create()
    return render(request, "index.html", {
        "products": products,
        "site": settings_obj,
        "builder_sizes": BuilderSize.objects.filter(is_active=True),
        "builder_toppings": BuilderTopping.objects.filter(is_active=True),
        "collections": collections,
    })


@require_POST
def create_order(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Невалидни данни."}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Невалидни данни."}, status=400)

    order_type = data.get("orderType")
    items = data.get("items") or []
    if order_type not in ("delivery", "pickup") or not isinstance(items, list) or not items:
        return JsonResponse({"error": "Невалидна поръчка."}, status=400)

    phone_value = data.get("customerPhone", "")
    if not isinstance(phone_value, str):
        return JsonResponse({"error": "Въведете телефонен номер с точно 10 цифри, започващ с 0."}, status=400)
    customer_phone = re.sub(r"\D", "", phone_value)
    if not re.fullmatch(r"0\d{9}", customer_phone):
        return JsonResponse({"error": "Въведете телефонен номер с точно 10 цифри, започващ с 0."}, status=400)

    try:
        total = sum(Decimal(str(item["price"])) * int(item["quantity"]) for item in items)
    except (KeyError, InvalidOperation, TypeError, ValueError):
        return JsonResponse({"error": "Невалидна поръчка."}, status=400)

    order = Order.objects.create(
        order_type=order_type,
        customer_name=data.get("customerName", "").strip(),
        customer_phone=customer_phone,
        delivery_address=data.get("address", "").strip(),
        pickup_location=data.get("pickupLocation", "").strip(),
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
