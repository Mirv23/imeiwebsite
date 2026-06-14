"""The verification engine.

Right now this returns a *deterministic mock* verdict derived from the IMEI, so
the demo runs end-to-end and the same IMEI always yields the same answer. When a
real provider (e.g. a carrier/GSMA lookup API) is ready, implement `run_lookup`
to call it and map the response into a `CheckResult` — the rest of the app
(views, templates, models) does not change.
"""
from __future__ import annotations

import hashlib

from .models import CheckResult, Order
from .validators import normalize_imei

# Apple TAC prefixes (first 8 digits) → marketing name, abbreviated sample set.
_KNOWN_MODELS = {
    "35328111": ("Apple", "iPhone 14 Pro"),
    "35693807": ("Apple", "iPhone 13"),
    "35846509": ("Apple", "iPhone 15 Pro Max"),
    "35238508": ("Samsung", "Galaxy S23 Ultra"),
    "86717003": ("Xiaomi", "Redmi Note 12"),
}


def _seed(imei: str) -> int:
    """Stable pseudo-random seed from the IMEI."""
    return int(hashlib.sha256(imei.encode()).hexdigest(), 16)


def _guess_model(imei: str) -> tuple[str, str]:
    prefix = imei[:8]
    if prefix in _KNOWN_MODELS:
        return _KNOWN_MODELS[prefix]
    # Fall back to a plausible brand based on the TAC.
    brands = ["Apple", "Samsung", "Google", "Xiaomi", "OnePlus"]
    return brands[_seed(imei) % len(brands)], "Model on file"


def run_lookup(order: Order) -> CheckResult:
    """Produce (and persist) the verdict for an order.

    TODO(backend): replace the mock block below with a real provider call,
    storing the untouched response in `raw_payload` and mapping fields.
    """
    imei = normalize_imei(order.imei)
    seed = _seed(imei + order.service.slug)
    brand, model = _guess_model(imei)

    # Deterministic bucket: ~70% clean, ~18% locked, ~12% flagged.
    bucket = seed % 100
    if bucket < 70:
        verdict = CheckResult.Verdict.CLEAN
        headline = "Clean. No blacklist, no lock."
        summary = "This device is safe to buy or activate on any carrier."
    elif bucket < 88:
        verdict = CheckResult.Verdict.LOCKED
        headline = "Locked. Activation Lock is on."
        summary = "Find My / iCloud is active. Ask the seller to sign out first."
    else:
        verdict = CheckResult.Verdict.FLAGGED
        headline = "Flagged. Reported lost or stolen."
        summary = "This device is on a blacklist. We strongly advise against buying it."

    fields = {
        "Brand": brand,
        "Model": model,
        "IMEI": imei,
        "Blacklist status": "Clear" if verdict == CheckResult.Verdict.CLEAN else "Reported",
        "SIM lock": "Unlocked" if seed % 3 else "Locked to carrier",
        "Find My / Activation Lock": "Off" if verdict != CheckResult.Verdict.LOCKED else "On",
        "Warranty": "Out of warranty" if seed % 2 else "In warranty",
    }

    result, _ = CheckResult.objects.update_or_create(
        order=order,
        defaults={
            "verdict": verdict,
            "headline": headline,
            "summary": summary,
            "fields": fields,
            "raw_payload": {"source": "mock-engine", "version": 1},
        },
    )
    order.mark_completed()
    return result
