import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import CustomerForm, TicketForm, WorkItemForm
from .models import Customer, Ticket, TicketEvent


def filtered_tickets(params):
    tickets = Ticket.objects.select_related("customer", "assigned_to")
    query = params.get("q", "").strip()[:120]
    status = params.get("status", "")
    priority = params.get("priority", "")
    overdue = params.get("overdue", "")
    if query:
        search = Q(title__icontains=query) | Q(issue__icontains=query) | Q(customer__name__icontains=query) | Q(customer__phone__icontains=query)
        if query.isdecimal():
            search |= Q(pk=int(query))
        tickets = tickets.filter(search)
    if status in Ticket.Status.values:
        tickets = tickets.filter(status=status)
    if priority in Ticket.Priority.values:
        tickets = tickets.filter(priority=priority)
    if overdue == "1":
        tickets = tickets.filter(due_date__lt=timezone.localdate()).exclude(status__in=[Ticket.Status.CLOSED, Ticket.Status.CANCELLED])
    return tickets


@login_required
def dashboard(request):
    open_tickets = Ticket.objects.exclude(status__in=[Ticket.Status.CLOSED, Ticket.Status.CANCELLED])
    today = timezone.localdate()
    status_counts = {row["status"]: row["total"] for row in Ticket.objects.values("status").annotate(total=Count("id"))}
    status_breakdown = [
        {"label": label, "count": status_counts.get(value, 0)}
        for value, label in Ticket.Status.choices
    ]
    total_tickets = sum(row["count"] for row in status_breakdown)
    for row in status_breakdown:
        row["width"] = round(row["count"] * 100 / total_tickets) if total_tickets else 0
    context = {
        "open_count": open_tickets.count(),
        "new_count": open_tickets.filter(status=Ticket.Status.NEW).count(),
        "ready_count": open_tickets.filter(status=Ticket.Status.READY).count(),
        "urgent_count": open_tickets.filter(priority=Ticket.Priority.HIGH).count(),
        "overdue_count": open_tickets.filter(due_date__lt=today).count(),
        "due_soon_count": open_tickets.filter(due_date__gte=today, due_date__lte=today + timedelta(days=7)).count(),
        "closed_month_count": Ticket.objects.filter(status=Ticket.Status.CLOSED, updated_at__gte=timezone.now() - timedelta(days=30)).count(),
        "status_breakdown": status_breakdown,
        "total_tickets": total_tickets,
        "recent_tickets": Ticket.objects.select_related("customer", "assigned_to")[:8],
        "recent_events": TicketEvent.objects.select_related("ticket", "actor")[:6],
    }
    return render(request, "desk/dashboard.html", context)


@login_required
def ticket_list(request):
    page = Paginator(filtered_tickets(request.GET), 12).get_page(request.GET.get("page"))
    return render(request, "desk/ticket_list.html", {
        "page": page,
        "query": request.GET.get("q", "")[:120],
        "selected_status": request.GET.get("status", ""),
        "selected_priority": request.GET.get("priority", ""),
        "selected_overdue": request.GET.get("overdue", ""),
        "statuses": Ticket.Status.choices,
        "priorities": Ticket.Priority.choices,
    })


@login_required
@require_GET
def ticket_export(request):
    """Export only the same filtered tickets the operator can see in the list."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="tickets.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Номер", "Устройство", "Клиент", "Статус", "Приоритет", "Срок", "Оценка"])

    def safe(value):
        text = str(value or "")
        return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text

    for ticket in filtered_tickets(request.GET).iterator():
        writer.writerow([
            ticket.pk, safe(ticket.title), safe(ticket.customer.name),
            ticket.get_status_display(), ticket.get_priority_display(),
            ticket.due_date.isoformat() if ticket.due_date else "", ticket.estimate,
        ])
    return response


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(
        Ticket.objects.select_related("customer", "assigned_to").prefetch_related("work_items", "events__actor"),
        pk=pk,
    )
    allowed = [(value, label) for value, label in Ticket.Status.choices if value in ticket.allowed_next_statuses]
    return render(request, "desk/ticket_detail.html", {
        "ticket": ticket,
        "allowed_statuses": allowed,
        "work_form": WorkItemForm(),
    })


@login_required
def ticket_create(request):
    form = TicketForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            ticket = form.save()
            TicketEvent.objects.create(ticket=ticket, actor=request.user, description="Заявка создана")
        messages.success(request, "Заявка создана")
        return redirect(ticket)
    return render(request, "desk/ticket_form.html", {"form": form, "heading": "Новая заявка", "submit_label": "Создать заявку"})


@login_required
def ticket_edit(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    form = TicketForm(request.POST or None, instance=ticket)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
            TicketEvent.objects.create(ticket=ticket, actor=request.user, description="Данные заявки обновлены")
        messages.success(request, "Изменения сохранены")
        return redirect(ticket)
    return render(request, "desk/ticket_form.html", {"form": form, "heading": f"Изменить заявку #{ticket.pk}", "submit_label": "Сохранить", "ticket": ticket})


@login_required
@require_POST
def ticket_status(request, pk):
    with transaction.atomic():
        ticket = get_object_or_404(Ticket.objects.select_for_update(), pk=pk)
        new_status = request.POST.get("status")
        if new_status not in ticket.allowed_next_statuses:
            messages.error(request, "Такой переход статуса недоступен")
        else:
            old_label = ticket.get_status_display()
            ticket.status = new_status
            ticket.save(update_fields=["status", "updated_at"])
            TicketEvent.objects.create(ticket=ticket, actor=request.user, description=f"Статус: {old_label} → {ticket.get_status_display()}")
            messages.success(request, "Статус обновлён")
    return redirect(ticket)


@login_required
@require_POST
def work_item_create(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    form = WorkItemForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            item = form.save(commit=False)
            item.ticket = ticket
            item.save()
            TicketEvent.objects.create(ticket=ticket, actor=request.user, description=f"Добавлена позиция: {item.description}")
        messages.success(request, "Позиция добавлена")
    else:
        messages.error(request, "Проверьте описание, количество и цену")
    return redirect(ticket)


@login_required
def customer_list(request):
    query = request.GET.get("q", "").strip()[:120]
    customers = Customer.objects.all()
    if query:
        customers = customers.filter(Q(name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query))
    page = Paginator(customers, 20).get_page(request.GET.get("page"))
    return render(request, "desk/customer_list.html", {"page": page, "query": query})


@login_required
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Клиент добавлен. Теперь можно создать заявку")
        return redirect("ticket_create")
    return render(request, "desk/customer_form.html", {"form": form})


def ticket_data(ticket):
    return {
        "id": ticket.pk,
        "title": ticket.title,
        "issue": ticket.issue,
        "status": ticket.status,
        "priority": ticket.priority,
        "customer": {"id": ticket.customer_id, "name": ticket.customer.name},
        "assigned_to": ticket.assigned_to.username if ticket.assigned_to else None,
        "estimate": str(ticket.estimate),
        "due_date": ticket.due_date.isoformat() if ticket.due_date else None,
        "created_at": ticket.created_at.isoformat(),
    }


@login_required
@require_GET
def api_ticket_list(request):
    page = Paginator(filtered_tickets(request.GET), 20).get_page(request.GET.get("page"))
    return JsonResponse({"count": page.paginator.count, "page": page.number, "pages": page.paginator.num_pages, "results": [ticket_data(ticket) for ticket in page]})


@login_required
@require_GET
def api_ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related("customer", "assigned_to"), pk=pk)
    return JsonResponse(ticket_data(ticket))
