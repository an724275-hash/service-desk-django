from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Customer(models.Model):
    name = models.CharField("Имя", max_length=120)
    phone = models.CharField("Телефон", max_length=32)
    email = models.EmailField("Email", blank=True)
    notes = models.TextField("Примечание", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return self.name


class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        DIAGNOSING = "diagnosing", "Диагностика"
        WAITING = "waiting", "Ждём запчасти"
        IN_PROGRESS = "in_progress", "В работе"
        READY = "ready", "Готово"
        CLOSED = "closed", "Закрыта"
        CANCELLED = "cancelled", "Отменена"

    class Priority(models.TextChoices):
        LOW = "low", "Обычная"
        MEDIUM = "medium", "Важная"
        HIGH = "high", "Срочная"

    TRANSITIONS = {
        Status.NEW: {Status.DIAGNOSING, Status.CANCELLED},
        Status.DIAGNOSING: {Status.WAITING, Status.IN_PROGRESS, Status.CANCELLED},
        Status.WAITING: {Status.IN_PROGRESS, Status.CANCELLED},
        Status.IN_PROGRESS: {Status.READY, Status.CANCELLED},
        Status.READY: {Status.CLOSED, Status.IN_PROGRESS},
        Status.CLOSED: set(),
        Status.CANCELLED: set(),
    }

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="tickets", verbose_name="Клиент")
    title = models.CharField("Устройство или задача", max_length=160)
    issue = models.TextField("Описание проблемы")
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    priority = models.CharField("Приоритет", max_length=10, choices=Priority.choices, default=Priority.LOW, db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets", verbose_name="Исполнитель")
    due_date = models.DateField("Срок", null=True, blank=True)
    estimate = models.DecimalField("Предварительная оценка", max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0"))])
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def __str__(self):
        return f"#{self.pk} {self.title}"

    def get_absolute_url(self):
        return reverse("ticket_detail", args=[self.pk])

    @property
    def final_amount(self):
        return sum((item.amount for item in self.work_items.all()), Decimal("0.00"))

    @property
    def allowed_next_statuses(self):
        return self.TRANSITIONS[self.status]


class WorkItem(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="work_items", verbose_name="Заявка")
    description = models.CharField("Работа или материал", max_length=160)
    quantity = models.PositiveIntegerField("Количество", default=1)
    unit_price = models.DecimalField("Цена за единицу", max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Позиция сметы"
        verbose_name_plural = "Позиции сметы"

    @property
    def amount(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return self.description


class TicketEvent(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="events", verbose_name="Заявка")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ticket_events", verbose_name="Сотрудник")
    description = models.CharField("Событие", max_length=240)
    created_at = models.DateTimeField("Время", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Событие"
        verbose_name_plural = "История заявки"

    def __str__(self):
        return self.description

