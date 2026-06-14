from django.conf import settings


def brand(request):
    """Expose brand/business constants to every template."""
    return {
        "BRAND": {
            "name": "Veridex",
            "tagline": "Every IMEI, verified in seconds.",
            "support_email": settings.VERIDEX["support_email"],
            "currency_symbol": settings.VERIDEX["currency_symbol"],
        }
    }
