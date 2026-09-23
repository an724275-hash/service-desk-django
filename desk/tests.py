from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Customer, Ticket, TicketEvent, WorkItem


class DeskTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="operator", password="strong-demo-pass-984")
        cls.customer = Customer.objects.create(name="Тестовый клиент", phone="+7 900 000-00-00")
        cls.ticket = Ticket.objects.create(customer=cls.customer, title="Проверка устройства", issue="Не включается")

    def setUp(self):
        self.client.force_login(self.user)

    def test_anonymous_user_cannot_read_dashboard_or_api(self):
        self.client.logout()
        for url in [reverse("dashboard"), reverse("ticket_list"), reverse("ticket_detail", args=[self.ticket.pk]), reverse("api_ticket_list")]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/accounts/login/", response.url)

    def test_ticket_creation_records_event(self):
        response = self.client.post(reverse("ticket_create"), {
            "customer": self.customer.pk, "title": "Замена экрана", "issue": "Трещина",
            "priority": Ticket.Priority.HIGH, "assigned_to": "", "due_date": "", "estimate": "3500.00",
        })
        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(title="Замена экрана")
        self.assertEqual(ticket.estimate, Decimal("3500.00"))
        self.assertEqual(ticket.events.count(), 1)

    def test_status_follows_allowed_transitions_and_records_history(self):
        url = reverse("ticket_status", args=[self.ticket.pk])
        response = self.client.post(url, {"status": Ticket.Status.DIAGNOSING})
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.DIAGNOSING)
        self.assertEqual(TicketEvent.objects.filter(ticket=self.ticket).count(), 1)
        self.client.post(url, {"status": Ticket.Status.CLOSED})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.DIAGNOSING)
        self.assertEqual(TicketEvent.objects.filter(ticket=self.ticket).count(), 1)

    def test_status_rejects_get_request(self):
        response = self.client.get(reverse("ticket_status", args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 405)

    def test_work_item_total_and_invalid_amount(self):
        url = reverse("work_item_create", args=[self.ticket.pk])
        self.client.post(url, {"description": "Диагностика", "quantity": "2", "unit_price": "1200.50"})
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.final_amount, Decimal("2401.00"))
        self.assertEqual(self.ticket.events.count(), 1)
        self.client.post(url, {"description": "Ошибка", "quantity": "1", "unit_price": "-100"})
        self.assertEqual(WorkItem.objects.filter(ticket=self.ticket).count(), 1)

    def test_list_filters_and_read_only_api(self):
        response = self.client.get(reverse("ticket_list"), {"q": "Проверка", "status": Ticket.Status.NEW})
        self.assertContains(response, "Проверка устройства")
        response = self.client.get(reverse("api_ticket_list"), {"q": str(self.ticket.pk)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["customer"]["name"], "Тестовый клиент")
        self.assertEqual(self.client.post(reverse("api_ticket_list")).status_code, 405)

    def test_customer_create_redirects_to_ticket_form(self):
        response = self.client.post(reverse("customer_create"), {"name": "Новый клиент", "phone": "+7 900 000-00-01"})
        self.assertRedirects(response, reverse("ticket_create"))
        self.assertTrue(Customer.objects.filter(name="Новый клиент").exists())

    def test_detail_renders_estimate_and_history(self):
        WorkItem.objects.create(ticket=self.ticket, description="Работа", quantity=1, unit_price=Decimal("900.00"))
        TicketEvent.objects.create(ticket=self.ticket, actor=self.user, description="Заявка создана")
        TicketEvent.objects.create(ticket=self.ticket, actor=None, description="Системное событие")
        response = self.client.get(reverse("ticket_detail", args=[self.ticket.pk]))
        self.assertContains(response, "Заявка создана")
        self.assertContains(response, "Системное событие")
        self.assertContains(response, "900")

    def test_overdue_filter_and_csv_export(self):
        self.ticket.title = '=SUM(1,1)'
        self.ticket.due_date = timezone.localdate() - timedelta(days=1)
        self.ticket.save()
        Ticket.objects.create(customer=self.customer, title='Будущий ремонт', issue='Тест', due_date=timezone.localdate() + timedelta(days=1))
        filtered = self.client.get(reverse('ticket_list'), {'overdue': '1'})
        self.assertContains(filtered, '=SUM(1,1)')
        self.assertNotContains(filtered, 'Будущий ремонт')
        exported = self.client.get(reverse('ticket_export'), {'overdue': '1'})
        self.assertEqual(exported.status_code, 200)
        self.assertIn('text/csv', exported['Content-Type'])
        self.assertIn("'=SUM(1,1)", exported.content.decode('utf-8-sig'))
        self.assertNotIn('Будущий ремонт', exported.content.decode('utf-8-sig'))

    def test_anonymous_user_cannot_export(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('ticket_export')).status_code, 302)
