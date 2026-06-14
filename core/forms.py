from django import forms

from .models import Order, Service
from .validators import normalize_imei, validate_imei


class OrderForm(forms.ModelForm):
    """Place-order form: pick a service, enter an IMEI, optional email."""

    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True),
        widget=forms.HiddenInput,
    )

    class Meta:
        model = Order
        fields = ["service", "imei", "email"]
        widgets = {
            "imei": forms.TextInput(
                attrs={
                    "inputmode": "numeric",
                    "autocomplete": "off",
                    "placeholder": "354 8650 9123 4567",
                    "maxlength": "20",
                    "class": "imei-input",
                    "aria-describedby": "imei-help",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "inputmode": "email",
                    "autocomplete": "email",
                    "placeholder": "you@email.com (optional)",
                    "class": "field-input",
                }
            ),
        }

    def clean_imei(self):
        raw = self.cleaned_data["imei"]
        validate_imei(raw)
        return normalize_imei(raw)

    def save(self, commit=True):
        order = super().save(commit=False)
        order.price_paid = order.service.price
        order.status = Order.Status.PROCESSING
        if commit:
            order.save()
        return order
