import logging
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.cache import cache
from django.db.models import Min
from django.shortcuts import get_object_or_404, redirect, render

from .forms import OrderForm
from .models import Order, Service, ServiceCategory
from .moncash import MonCashClient, MonCashError
from .services import run_lookup

logger = logging.getLogger(__name__)

# Rate limit for the (DB-writing, provider-billable-later) check endpoint.
_RATE_LIMIT = 20      # allowed submissions per window, per client
_RATE_WINDOW = 3600   # seconds


def _client_ip(request) -> str:
    """Best-effort client IP behind Vercel's proxy (X-Forwarded-For)."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or "unknown"


def _rate_limited(request) -> bool:
    """Count submissions per client in a rolling window; True if over budget."""
    key = f"verify-rate:{_client_ip(request)}"
    count = cache.get(key, 0)
    if count >= _RATE_LIMIT:
        return True
    cache.set(key, count + 1, _RATE_WINDOW)
    return False


def home(request):
    featured = Service.objects.filter(is_active=True, is_featured=True)[:6]
    cheapest = Service.objects.filter(is_active=True).aggregate(p=Min("price"))["p"]
    return render(
        request,
        "pages/home.html",
        {"featured": featured, "cheapest": cheapest},
    )


def services(request):
    categories = (
        ServiceCategory.objects.prefetch_related("services")
        .filter(services__is_active=True)
        .distinct()
    )
    return render(request, "pages/services.html", {"categories": categories})


def place_order(request):
    """Choose service → enter IMEI → pay with MonCash → run the check.

    When MonCash isn't configured (no credentials), the check runs for free —
    the same demo flow as before — so the site keeps working out of the box.
    """
    preselect = request.GET.get("service")
    active_services = Service.objects.filter(is_active=True)
    moncash = MonCashClient()

    if request.method == "POST":
        if _rate_limited(request):
            messages.error(
                request,
                "Too many checks from your connection in a short time. "
                "Please wait a little and try again.",
            )
            form = OrderForm(request.POST)
        else:
            form = OrderForm(request.POST)
            if form.is_valid():
                order = form.save()
                if moncash.configured:
                    return _start_payment(request, order, moncash)
                # No payment configured → free/demo flow.
                run_lookup(order)
                return redirect(order.get_absolute_url())
            messages.error(request, "Please fix the highlighted fields.")
    else:
        initial = {}
        if preselect:
            match = active_services.filter(slug=preselect).first()
            if match:
                initial["service"] = match
        form = OrderForm(initial=initial)

    selected = None
    if preselect:
        selected = active_services.filter(slug=preselect).first()

    return render(
        request,
        "pages/place_order.html",
        {
            "form": form,
            "services": active_services,
            "selected": selected,
            "payment_enabled": moncash.configured,
        },
    )


def _start_payment(request, order, moncash):
    """Create a MonCash payment for `order` and redirect to the gateway."""
    try:
        payment = moncash.create_payment(order.price_paid, order.reference)
    except MonCashError:
        logger.exception("MonCash CreatePayment failed for %s", order.reference)
        order.payment_status = Order.PaymentStatus.FAILED
        order.save(update_fields=["payment_status"])
        messages.error(
            request,
            "We couldn't start the payment just now. Please try again in a moment.",
        )
        return redirect("place_order")

    order.payment_status = Order.PaymentStatus.AWAITING
    order.save(update_fields=["payment_status"])
    # Remember which order this browser is paying for, to confirm on return.
    request.session["moncash_order_ref"] = order.reference
    return redirect(payment["redirect_url"])


def payment_return(request):
    """Return URL after MonCash. Confirm the payment server-side, then deliver.

    Configure this URL as the return URL in the MonCash business portal:
        https://<your-domain>/payment/return/
    """
    reference = request.GET.get("orderId") or request.session.get("moncash_order_ref")
    if not reference:
        messages.error(request, "We couldn't identify your payment. Please try again.")
        return redirect("place_order")

    order = get_object_or_404(
        Order.objects.select_related("service"), reference=reference
    )

    # Already delivered — just show the result (idempotent on refresh/back).
    if order.is_paid:
        return redirect(order.get_absolute_url())

    moncash = MonCashClient()
    try:
        payment = moncash.retrieve_order_payment(order.reference)
    except MonCashError:
        logger.exception("MonCash RetrieveOrderPayment failed for %s", order.reference)
        payment = None

    if _payment_confirmed(payment, order.price_paid):
        order.mark_paid(
            transaction_id=str(payment.get("transaction_id", "")),
            payer=str(payment.get("payer", "")),
        )
        run_lookup(order)
        request.session.pop("moncash_order_ref", None)
        return redirect(order.get_absolute_url())

    # Not confirmed: leave it awaiting (the buyer may retry / it may settle).
    return render(request, "pages/payment_pending.html", {"order": order})


def _payment_confirmed(payment, expected_amount: Decimal) -> bool:
    """True only if MonCash reports success AND the amount matches what we sent."""
    if not payment:
        return False
    if str(payment.get("message", "")).lower() != "successful":
        return False
    try:
        cost = Decimal(str(payment.get("cost", "0")))
    except (InvalidOperation, TypeError):
        return False
    # We sent `expected_amount`; MonCash echoes it back as `cost`. Guard against
    # a tampered/short payment. Small tolerance for float round-tripping.
    return abs(cost - Decimal(expected_amount)) < Decimal("0.01")


def order_result(request, reference):
    order = get_object_or_404(
        Order.objects.select_related("service", "result"), reference=reference
    )
    return render(request, "pages/result.html", {"order": order})
