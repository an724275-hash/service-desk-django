from django import forms
from django.contrib.auth import get_user_model

from .models import Customer, Ticket, WorkItem


class StyledFormMixin:
    def style_fields(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field-input")


class CustomerForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "email", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class TicketForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["customer", "title", "issue", "priority", "assigned_to", "due_date", "estimate"]
        widgets = {
            "issue": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = get_user_model().objects.filter(is_active=True).order_by("username")
        self.fields["assigned_to"].empty_label = "Не назначен"
        self.fields["due_date"].input_formats = ["%Y-%m-%d"]
        self.style_fields()


class WorkItemForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = WorkItem
        fields = ["description", "quantity", "unit_price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()

