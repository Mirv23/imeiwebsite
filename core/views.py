from django.contrib import messages
from django.core.cache import cache
from django.db.models import Min
from django.shortcuts import get_object_or_404, redirect, render

from .forms import OrderForm
from .models import Order, Service, ServiceCategory
from .services import run_lookup

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
    """Single-screen flow: choose service → enter IMEI → run the check."""
    preselect = request.GET.get("service")
    active_services = Service.objects.filter(is_active=True)

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
                run_lookup(order)  # mock today, real provider later
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
        {"form": form, "services": active_services, "selected": selected},
    )


def order_result(request, reference):
    order = get_object_or_404(
        Order.objects.select_related("service", "result"), reference=reference
    )
    return render(request, "pages/result.html", {"order": order})
