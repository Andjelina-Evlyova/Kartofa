import json
from decimal import Decimal

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Order, SiteSettings


class CreateOrderTests(TestCase):
    def test_create_order_returns_json_and_saves_order(self):
        response = self.client.post(
            reverse("create_order"),
            data=json.dumps({
                "orderType": "pickup",
                "customerName": "Тест Клиент",
                "customerPhone": "0888000000",
                "pickupLocation": "Тестов обект",
                "items": [{"name": "Тестов продукт", "price": 5.5, "quantity": 2}],
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertFalse(response.json()["notificationSent"])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.get().total, Decimal("11.00"))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_create_order_sends_email_notification_automatically(self):
        SiteSettings.objects.create(order_notification_email="orders@example.com")

        response = self.client.post(
            reverse("create_order"),
            data=json.dumps({
                "orderType": "pickup",
                "customerName": "Тест Клиент",
                "customerPhone": "0888000000",
                "pickupLocation": "Тестов обект",
                "items": [{"name": "Тестов продукт", "price": 5.5, "quantity": 2}],
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["emailSent"])
        self.assertTrue(response.json()["notificationSent"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["orders@example.com"])
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
        response = self.client.post(
            reverse("create_order"),
            data=json.dumps({
                "orderType": "pickup",
                "customerName": "Тест Клиент",
                "customerPhone": "088800000",
                "pickupLocation": "Тестов обект",
                "items": [{"name": "Тестов продукт", "price": 5.5, "quantity": 2}],
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_create_order_accepts_formatted_ten_digit_phone_and_stores_digits(self):
        response = self.client.post(
            reverse("create_order"),
            data=json.dumps({
                "orderType": "pickup",
                "customerName": "Тест Клиент",
                "customerPhone": "0888-000-000",
                "pickupLocation": "Тестов обект",
                "items": [{"name": "Тестов продукт", "price": 5.5, "quantity": 2}],
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.get().customer_phone, "0888000000")
