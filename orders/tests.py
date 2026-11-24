import json
from decimal import Decimal

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (
    BuilderSize,
    BuilderTopping,
    MenuCollection,
    Order,
    Product,
    SiteSettings,
)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CreateOrderTests(TestCase):
    def setUp(self):
        self.site = SiteSettings.objects.create(
            order_notification_email="",
            address="Тест адрес 1",
            second_address="Тест адрес 2",
        )
        self.collection = MenuCollection.objects.create(name="Меню", slug="menu")
        self.product = Product.objects.create(
            name="Картоф с пиле",
            collection=self.collection,
            price=Decimal("5.50"),
            is_available=True,
        )

    def make_payload(self, **overrides):
        payload = {
            "orderType": "pickup",
            "customerName": "Тест Клиент",
            "customerPhone": "0888000000",
            "pickupLocation": self.site.address,
            "items": [{
                "type": "product",
                "productId": self.product.pk,
                "quantity": 2,
            }],
        }
        payload.update(overrides)
        return payload

    def post_order(self, payload):
        return self.client.post(
            reverse("create_order"),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_create_order_returns_json_and_saves_order(self):
        response = self.post_order(self.make_payload())

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertTrue(response.json()["emailSent"])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.get().total, Decimal("11.00"))
        self.assertEqual(
            Order.objects.get().items,
            [{"name": "Картоф с пиле", "price": "5.50", "quantity": 2}],
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_create_order_sends_email_notification_automatically(self):
        self.site.order_notification_email = "orders@example.com"
        self.site.save()
        response = self.post_order(self.make_payload())

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["emailSent"])
        self.assertTrue(response.json()["notificationSent"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["aevlyovva@gmail.com"])
        self.assertIn("Нова поръчка #1", mail.outbox[0].subject)

    def test_non_object_json_returns_json_error(self):
        response = self.client.post(
            reverse("create_order"),
            data="[]",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Невалидни данни.")

    def test_create_order_rejects_phone_with_wrong_number_of_digits(self):
        response = self.post_order(self.make_payload(customerPhone="088800000"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_formatted_phone_is_normalized_before_saving(self):
        response = self.post_order(self.make_payload(customerPhone="0888-000-000"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.get().customer_phone, "0888000000")

    def test_product_price_and_name_are_taken_from_database(self):
        payload = self.make_payload(items=[{
            "type": "product",
            "productId": self.product.pk,
            "quantity": 2,
            "price": "0.01",
            "name": "Манипулиран продукт",
        }])
        response = self.post_order(payload)

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get()
        self.assertEqual(order.total, Decimal("11.00"))
        self.assertEqual(order.items[0]["name"], "Картоф с пиле")
        self.assertEqual(order.items[0]["price"], "5.50")

    def test_order_rejects_unknown_and_unavailable_products(self):
        payload = self.make_payload(items=[{
            "type": "product",
            "productId": self.product.pk + 100,
            "quantity": 1,
        }])
        response = self.post_order(payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_rejects_non_positive_quantity(self):
        response = self.post_order(self.make_payload(items=[{
            "type": "product",
            "productId": self.product.pk,
            "quantity": -1,
        }]))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_builder_price_and_toppings_are_taken_from_database(self):
        size = BuilderSize.objects.create(name="2 добавки", topping_count=2, price=Decimal("6.00"))
        bacon = BuilderTopping.objects.create(name="Бекон", extra_price=Decimal("0.50"))
        cheese = BuilderTopping.objects.create(name="Кашкавал", extra_price=Decimal("0.25"))
        payload = self.make_payload(items=[{
            "type": "builder",
            "sizeId": size.pk,
            "base": "large",
            "toppingIds": [bacon.pk, cheese.pk],
            "quantity": 1,
            "price": "0.01",
        }])

        response = self.post_order(payload)

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get()
        self.assertEqual(order.total, Decimal("8.25"))
        self.assertIn("Бекон", order.items[0]["name"])
        self.assertEqual(order.items[0]["price"], "8.25")

    def test_delivery_requires_address(self):
        response = self.post_order(self.make_payload(
            orderType="delivery",
            address="  ",
        ))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_pickup_requires_configured_location(self):
        response = self.post_order(self.make_payload(pickupLocation="Невалиден адрес"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
