from django.contrib import admin

from .models import CheckResult, Order, Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "delivery_time", "is_active", "is_featured")
    list_filter = ("category", "is_active", "is_featured")
    list_editable = ("price", "is_active", "is_featured")
    prepopulated_fields = {"slug": ("name",)}


class CheckResultInline(admin.StackedInline):
    model = CheckResult
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "service", "imei", "payment_status", "status",
        "price_paid", "created_at",
    )
    list_filter = ("payment_status", "status", "service")
    search_fields = ("reference", "imei", "email", "moncash_transaction_id")
    readonly_fields = (
        "reference", "created_at", "completed_at", "paid_at",
        "moncash_transaction_id", "moncash_payer",
    )
    inlines = [CheckResultInline]
