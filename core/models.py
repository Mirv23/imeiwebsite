"""Data model for the Veridex IMEI verification service.

Designed to drop a real lookup provider in later: an `Order` records what the
user asked for, a `CheckResult` stores both a structured verdict *and* the raw
provider payload (`raw_payload`) so nothing is lost when a real API is wired up.
"""
import secrets

from django.db import models
from django.urls import reverse
from django.utils import timezone

from .validators import validate_imei


def make_reference() -> str:
    """Unguessable, human-shareable order reference, e.g. VDX-7F3A9C1D4B2E.

    The result page is reachable by reference alone (no login), so the
    reference is the only thing standing between a stranger and someone
    else's lookup. 6 bytes = 48 bits of entropy makes enumeration
    infeasible. "VDX-" + 12 hex chars = 16 chars, the field's max_length.
    """
    return "VDX-" + secrets.token_hex(6).upper()


class ServiceCategory(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    tagline = models.CharField(max_length=160, blank=True)
    icon = models.CharField(
        max_length=40,
        default="shield",
        help_text="Icon key resolved by the {% icon %} template tag.",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Service categories"

    def __str__(self) -> str:
        return self.name


class Service(models.Model):
    category = models.ForeignKey(
        ServiceCategory, related_name="services", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    short_description = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    delivery_time = models.CharField(max_length=40, default="1–5 min")
    success_rate = models.PositiveSmallIntegerField(
        default=99, help_text="Displayed success rate, percent."
    )
    icon = models.CharField(max_length=40, default="search")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("place_order") + f"?service={self.slug}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        AWAITING = "awaiting", "Awaiting payment"  # redirected to MonCash
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    reference = models.CharField(
        max_length=16, unique=True, default=make_reference, editable=False
    )
    service = models.ForeignKey(
        Service, related_name="orders", on_delete=models.PROTECT
    )
    imei = models.CharField(max_length=17, validators=[validate_imei])
    email = models.EmailField(blank=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )
    price_paid = models.DecimalField(max_digits=8, decimal_places=2)
    # --- Payment (MonCash) ---
    payment_status = models.CharField(
        max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID
    )
    moncash_transaction_id = models.CharField(max_length=64, blank=True)
    moncash_payer = models.CharField(max_length=32, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.reference} · {self.service.name}"

    def get_absolute_url(self) -> str:
        return reverse("order_result", args=[self.reference])

    @property
    def is_paid(self) -> bool:
        return self.payment_status == self.PaymentStatus.PAID

    def mark_paid(self, transaction_id: str = "", payer: str = "") -> None:
        self.payment_status = self.PaymentStatus.PAID
        self.moncash_transaction_id = transaction_id or ""
        self.moncash_payer = payer or ""
        self.paid_at = timezone.now()
        self.save(
            update_fields=[
                "payment_status", "moncash_transaction_id",
                "moncash_payer", "paid_at",
            ]
        )

    def mark_completed(self) -> None:
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])


class CheckResult(models.Model):
    """The verdict for an order.

    `verdict` is the one-word read the UI leads with; `fields` is structured
    detail; `raw_payload` is reserved for the real provider response.
    """

    class Verdict(models.TextChoices):
        CLEAN = "clean", "Clean"
        FLAGGED = "flagged", "Flagged"
        LOCKED = "locked", "Locked"
        UNKNOWN = "unknown", "Unknown"

    order = models.OneToOneField(
        Order, related_name="result", on_delete=models.CASCADE
    )
    verdict = models.CharField(
        max_length=10, choices=Verdict.choices, default=Verdict.UNKNOWN
    )
    headline = models.CharField(max_length=160)
    summary = models.CharField(max_length=240, blank=True)
    fields = models.JSONField(default=dict, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.order.reference} → {self.get_verdict_display()}"
