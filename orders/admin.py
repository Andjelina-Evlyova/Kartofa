from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.html import format_html
from .models import BuilderSize, BuilderTopping, MenuCollection, Order, Product, SiteSettings


class SuperuserAdminSite(admin.AdminSite):
    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser


private_admin_site = SuperuserAdminSite(name="admin")
private_admin_site.register(get_user_model())
private_admin_site.register(Group)


@admin.register(MenuCollection, site=private_admin_site)
class MenuCollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(SiteSettings, site=private_admin_site)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Брандинг", {"fields": ("brand_name", "brand_location", "phone", "address", "second_address")}),
        ("Известия", {"fields": ("order_notification_email",)}),
        ("Начален банер", {"fields": ("hero_kicker", "hero_title", "hero_text", "hero_button_text", "hero_image")}),
        ("Меню и конструктор", {"fields": ("menu_kicker", "menu_title", "builder_kicker", "builder_title", "builder_text")}),
        ("За нас и футър", {"fields": ("about_title", "about_text", "footer_text", "weekday_hours", "weekend_hours", "copyright_text")}),
        ("Социални мрежи", {"fields": ("instagram_url", "facebook_url", "tiktok_url")}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Product, site=private_admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "collection", "price", "is_available", "is_featured", "sort_order")
    list_filter = ("collection", "is_available", "is_featured")
    list_editable = ("is_available", "is_featured", "sort_order")
    search_fields = ("name", "description")
    fieldsets = (
        ("Основна информация", {
            "fields": (
                "name",
                "collection",
                "description",
                "price",
            )
        }),
        ("Снимка", {
            "fields": ("image", "image_preview"),
            "description": "Изберете нов файл тук, за да смените снимката на вече създаден продукт.",
        }),
        ("Публикуване", {
            "fields": ("is_available", "is_featured", "sort_order"),
        }),
    )
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if not obj.image:
            return "Няма качена снимка."
        return format_html(
            '<img src="{}" style="max-width:280px;max-height:180px;object-fit:cover;border-radius:12px;">',
            obj.image.url,
        )
    image_preview.short_description = "Преглед"
    image_preview.allow_tags = True


@admin.register(BuilderSize, site=private_admin_site)
class BuilderSizeAdmin(admin.ModelAdmin):
    list_display = ("name", "topping_count", "price", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    list_filter = ("is_active",)


@admin.register(BuilderTopping, site=private_admin_site)
class BuilderToppingAdmin(admin.ModelAdmin):
    list_display = ("name", "extra_price", "is_active", "sort_order")
    list_editable = ("extra_price", "is_active", "sort_order")
    list_filter = ("is_active",)

@admin.register(Order, site=private_admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "order_type", "customer_name", "customer_phone", "status", "ready_in_minutes", "total")
    list_filter = ("order_type", "status", "pickup_location")
    search_fields = ("id", "customer_name", "customer_phone", "delivery_address")
    readonly_fields = ("created_at", "items", "total")
    fieldsets = (
        ("Детайли за поръчката", {
            "fields": ("created_at", "order_type", "status", "items", "total")
        }),
        ("Клиент и получаване", {
            "fields": ("customer_name", "customer_phone", "delivery_address", "pickup_location")
        }),
        ("Приготовяне", {
            "fields": ("ready_in_minutes", "staff_note")
        }),
    )