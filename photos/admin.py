from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """Admin interface for Photo model"""

    list_display = [
        "get_thumbnail",
        "title",
        "user",
        "camera_display",
        "exposure_display",
        "date_taken",
        "file_size_mb",
        "is_raw",
        "is_public",
    ]

    list_filter = [
        "is_raw",
        "is_public",
        "is_featured",
        "camera_make",
        "camera_model",
        "date_taken",
        "created_at",
        "file_extension",
    ]

    search_fields = [
        "title",
        "description",
        "tags",
        "user__username",
        "user__email",
        "camera_make",
        "camera_model",
        "lens_model",
    ]

    readonly_fields = [
        "file_size",
        "file_extension",
        "width",
        "height",
        "created_at",
        "updated_at",
        "camera_make",
        "camera_model",
        "lens_make",
        "lens_model",
        "focal_length",
        "shutter_speed",
        "aperture",
        "iso",
        "exposure_bias",
        "white_balance",
        "latitude",
        "longitude",
        "altitude",
        "date_taken",
    ]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "user",
                    "title",
                    "description",
                    "tags",
                    "is_public",
                    "is_featured",
                )
            },
        ),
        (
            "File Information",
            {
                "fields": (
                    "original_file",
                    "thumbnail",
                    "file_size",
                    "file_extension",
                    "is_raw",
                )
            },
        ),
        ("Image Dimensions", {"fields": ("width", "height")}),
        (
            "Camera & Lens",
            {
                "fields": (
                    "camera_make",
                    "camera_model",
                    "lens_make",
                    "lens_model",
                    "focal_length",
                    "focal_length_35mm",
                )
            },
        ),
        (
            "Exposure Settings",
            {
                "fields": (
                    "shutter_speed",
                    "aperture",
                    "iso",
                    "exposure_bias",
                    "exposure_mode",
                    "metering_mode",
                )
            },
        ),
        (
            "Image Settings",
            {"fields": ("white_balance", "color_space", "flash", "digital_zoom_ratio")},
        ),
        (
            "Location Data",
            {"fields": ("latitude", "longitude", "altitude", "location_description")},
        ),
        ("Time Information", {"fields": ("date_taken", "date_modified")}),
        ("Additional Metadata", {"fields": ("software_used", "copyright")}),
        (
            "System Information",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    list_per_page = 50
    ordering = ["-created_at"]

    def get_thumbnail(self, obj):
        """Display thumbnail in admin list"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px;" />',
                obj.thumbnail.url,
            )
        elif obj.original_file:
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px;" />',
                obj.original_file.url,
            )
        return "No image"

    get_thumbnail.short_description = "Thumbnail"
    get_thumbnail.admin_order_field = "original_file"

    def camera_display(self, obj):
        """Display camera information"""
        if obj.camera_make and obj.camera_model:
            return f"{obj.camera_make} {obj.camera_model}"
        elif obj.camera_make:
            return obj.camera_make
        elif obj.camera_model:
            return obj.camera_model
        return "Unknown"

    camera_display.short_description = "Camera"
    camera_display.admin_order_field = "camera_make"

    def exposure_display(self, obj):
        """Display exposure information"""
        parts = []
        if obj.shutter_speed:
            parts.append(f"1/{obj.shutter_speed}s")
        if obj.aperture:
            parts.append(f"f/{obj.aperture}")
        if obj.iso:
            parts.append(f"ISO {obj.iso}")
        return " • ".join(parts) if parts else "Unknown"

    exposure_display.short_description = "Exposure"

    def file_size_mb(self, obj):
        """Display file size in MB"""
        return f"{obj.get_file_size_mb()} MB"

    file_size_mb.short_description = "Size"
    file_size_mb.admin_order_field = "file_size"

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related("user")

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly based on object state"""
        if obj:  # Editing existing object
            return self.readonly_fields + ("user", "original_file")
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        """Custom save logic"""
        if not change:  # New object
            # Set user if not provided
            if not obj.user:
                obj.user = request.user
        super().save_model(request, obj, form, change)

    actions = ["make_public", "make_private", "mark_featured", "mark_not_featured"]

    def make_public(self, request, queryset):
        """Make selected photos public"""
        updated = queryset.update(is_public=True)
        self.message_user(request, f"{updated} photo(s) marked as public.")

    make_public.short_description = "Mark selected photos as public"

    def make_private(self, request, queryset):
        """Make selected photos private"""
        updated = queryset.update(is_public=False)
        self.message_user(request, f"{updated} photo(s) marked as private.")

    make_private.short_description = "Mark selected photos as private"

    def mark_featured(self, request, queryset):
        """Mark selected photos as featured"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} photo(s) marked as featured.")

    mark_featured.short_description = "Mark selected photos as featured"

    def mark_not_featured(self, request, queryset):
        """Remove featured status from selected photos"""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"{updated} photo(s) unmarked as featured.")

    mark_not_featured.short_description = "Remove featured status from selected photos"

    class Media:
        css = {"all": ("admin/css/photo_admin.css",)}
        js = ("admin/js/photo_admin.js",)
