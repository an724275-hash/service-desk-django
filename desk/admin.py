from django.contrib import admin

from .models import Customer, Ticket, TicketEvent, WorkItem


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at")
    search_fields = ("name", "phone", "email")


class WorkItemInline(admin.TabularInline):
    model = WorkItem
    extra = 0


class EventInline(admin.TabularInline):
    model = TicketEvent
    extra = 0
    readonly_fields = ("actor", "description", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "customer", "status", "priority", "assigned_to", "created_at")
    list_filter = ("status", "priority", "created_at")
    search_fields = ("title", "issue", "customer__name", "customer__phone")
    autocomplete_fields = ("customer", "assigned_to")
    inlines = (WorkItemInline, EventInline)


@admin.register(TicketEvent)
class TicketEventAdmin(admin.ModelAdmin):
    list_display = ("ticket", "description", "actor", "created_at")
    search_fields = ("ticket__title", "description")
    readonly_fields = ("ticket", "actor", "description", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

