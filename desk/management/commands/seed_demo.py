import os
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from desk.models import Customer, Ticket, TicketEvent, WorkItem


SAMPLES = [
    ("Клиент 01", "+7 900 000-00-01", "Ноутбук не включается", "После обновления индикатор горит, экран остаётся чёрным.", Ticket.Status.NEW, Ticket.Priority.HIGH, Decimal("3200")),
    ("Клиент 02", "+7 900 000-00-02", "Замена аккумулятора", "Устройство быстро разряжается даже в режиме ожидания.", Ticket.Status.DIAGNOSING, Ticket.Priority.MEDIUM, Decimal("4800")),
    ("Клиент 03", "+7 900 000-00-03", "Монитор: нет изображения", "Питание есть, сигнал с компьютера не появляется.", Ticket.Status.WAITING, Ticket.Priority.LOW, Decimal("2500")),
    ("Клиент 04", "+7 900 000-00-04", "Чистка системы охлаждения", "Вентилятор шумит, корпус нагревается.", Ticket.Status.IN_PROGRESS, Ticket.Priority.MEDIUM, Decimal("3900")),
    ("Клиент 05", "+7 900 000-00-05", "Настройка рабочего ПК", "Нужна установка системы и перенос файлов.", Ticket.Status.READY, Ticket.Priority.LOW, Decimal("5200")),
    ("Клиент 06", "+7 900 000-00-06", "Восстановление разъёма", "Зарядка работает только при определённом положении кабеля.", Ticket.Status.IN_PROGRESS, Ticket.Priority.HIGH, Decimal("6400")),
]


class Command(BaseCommand):
    help = "Создать локальный демонстрационный набор данных"

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Демоданные разрешены только при DJANGO_DEBUG=1")
        password = os.getenv("DEMO_PASSWORD", "demo12345")
        user, _ = get_user_model().objects.get_or_create(username="demo", defaults={"first_name": "Демо", "last_name": "сотрудник"})
        user.set_password(password)
        user.save(update_fields=["password"])
        for name, phone, title, issue, status, priority, estimate in SAMPLES:
            customer, _ = Customer.objects.get_or_create(phone=phone, defaults={"name": name})
            ticket, created = Ticket.objects.get_or_create(
                customer=customer,
                title=title,
                defaults={"issue": issue, "status": status, "priority": priority, "estimate": estimate, "assigned_to": user},
            )
            if created:
                TicketEvent.objects.create(ticket=ticket, actor=user, description="Демозаявка создана")
                if status in {Ticket.Status.IN_PROGRESS, Ticket.Status.READY}:
                    WorkItem.objects.create(ticket=ticket, description="Диагностика", quantity=1, unit_price=Decimal("1200.00"))
        self.stdout.write(self.style.SUCCESS("Демоданные готовы. Логин: demo. Пароль: значение DEMO_PASSWORD или demo12345."))

