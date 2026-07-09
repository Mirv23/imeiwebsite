"""Idempotently seed the IMEI service catalog.

Run with:  python manage.py seed_services
Inspired by the breadth of a real IMEI-order page (carrier, blacklist,
Find My / iCloud, SIM-lock, warranty, model info, MDM).
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Service, ServiceCategory

CATEGORIES = [
    ("Theft & blacklist", "blacklist", "Was it reported lost or stolen?", "shield-check", 1),
    ("Locks & activation", "locks", "Can you actually set it up?", "lock", 2),
    ("Device & carrier info", "info", "See what the phone really is.", "smartphone", 3),
    ("Warranty & coverage", "warranty", "See what's still covered.", "clock", 4),
]

SERVICES = [
    # slug, name, category_slug, short, price, delivery, success, icon, featured
    ("blacklist-check", "Blacklist & Stolen Check", "blacklist",
     "Check global blacklists for a lost, stolen, or unpaid report before you pay.",
     "1.49", "30 sec – 2 min", 99, "ban", True),
    ("find-my-iphone", "Find My / iCloud Status", "locks",
     "See whether Activation Lock is still on before you buy.",
     "1.99", "Instant", 99, "lock", True),
    ("sim-lock-check", "SIM-Lock & Carrier", "locks",
     "Find out if the phone is tied to a network or open to any SIM.",
     "2.49", "1 – 5 min", 98, "sim", True),
    ("carrier-find", "Original Carrier & Country", "info",
     "See which carrier and country the device was first sold for.",
     "1.99", "1 – 10 min", 98, "globe", True),
    ("model-info", "Full Model & Specs", "info",
     "Read the model, color, storage, and manufacture date from the IMEI.",
     "0.99", "Instant", 99, "smartphone", True),
    ("mdm-check", "MDM / Organization Lock", "locks",
     "Spot a corporate MDM lock that can lock the phone after a reset.",
     "2.99", "2 – 10 min", 97, "fingerprint", False),
    ("warranty-check", "Warranty & Coverage", "warranty",
     "Look up warranty status, purchase date, and remaining coverage.",
     "1.49", "Instant", 99, "clock", True),
    ("replaced-check", "Replaced / Refurbished Flag", "warranty",
     "See whether the device was swapped or refurbished under warranty.",
     "1.29", "1 – 5 min", 98, "info", False),
]


class Command(BaseCommand):
    help = "Seed Veridex service categories and services."

    def handle(self, *args, **options):
        cats = {}
        for name, slug, tagline, icon, order in CATEGORIES:
            cat, _ = ServiceCategory.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "tagline": tagline, "icon": icon, "order": order},
            )
            cats[slug] = cat

        created = 0
        for order, row in enumerate(SERVICES, start=1):
            slug, name, cat_slug, short, price, delivery, success, icon, featured = row
            _, was_created = Service.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "category": cats[cat_slug],
                    "short_description": short,
                    "price": Decimal(price),
                    "delivery_time": delivery,
                    "success_rate": success,
                    "icon": icon,
                    "is_featured": featured,
                    "is_active": True,
                    "order": order,
                },
            )
            created += int(was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(cats)} categories and {len(SERVICES)} services "
                f"({created} new)."
            )
        )
