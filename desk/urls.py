from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tickets/", views.ticket_list, name="ticket_list"),
    path("tickets/new/", views.ticket_create, name="ticket_create"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:pk>/edit/", views.ticket_edit, name="ticket_edit"),
    path("tickets/<int:pk>/status/", views.ticket_status, name="ticket_status"),
    path("tickets/<int:pk>/work-items/", views.work_item_create, name="work_item_create"),
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/new/", views.customer_create, name="customer_create"),
    path("api/v1/tickets/", views.api_ticket_list, name="api_ticket_list"),
    path("api/v1/tickets/<int:pk>/", views.api_ticket_detail, name="api_ticket_detail"),
]

