import os
import uuid
from datetime import datetime
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from PIL import Image
import exifread
import rawpy
from io import BytesIO

User = get_user_model()


def photo_upload_path(instance, filename):
    """Generate upload path for photos: /media/photos/userid/filename"""
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("photos", str(instance.user.id), filename)


def thumbnail_upload_path(instance, filename):
    """Generate upload path for thumbnails"""
    ext = filename.split(".")[-1]
    filename = f"thumb_{uuid.uuid4()}.{ext}"
    return os.path.join("photos", str(instance.user.id), "thumbnails", filename)


class Photo(models.Model):
    """Professional photo model with EXIF data extraction"""

    # Basic photo information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="photos")
    title = models.CharField(max_length=200, blank=True, default="Untitled")
    description = models.TextField(blank=True, null=True)
    tags = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated tags"
    )

    # File information
    original_file = models.ImageField(upload_to=photo_upload_path, max_length=500)
    thumbnail = models.ImageField(
        upload_to=thumbnail_upload_path, max_length=500, blank=True, null=True
    )
    file_size = models.BigIntegerField(help_text="File size in bytes")
    file_extension = models.CharField(max_length=10)
    is_raw = models.BooleanField(default=False)

    # Image dimensions
    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)

    # EXIF Camera Data
    camera_make = models.CharField(max_length=100, blank=True)
    camera_model = models.CharField(max_length=100, blank=True)
    lens_make = models.CharField(max_length=100, blank=True)
    lens_model = models.CharField(max_length=100, blank=True)
    focal_length = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    focal_length_35mm = models.PositiveIntegerField(blank=True, null=True)

    # EXIF Exposure Data
    shutter_speed = models.CharField(max_length=50, blank=True)
    aperture = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )
    iso = models.PositiveIntegerField(blank=True, null=True)
    exposure_bias = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )
    exposure_mode = models.CharField(max_length=50, blank=True)
    metering_mode = models.CharField(max_length=50, blank=True)

    # EXIF Image Data
    white_balance = models.CharField(max_length=50, blank=True)
    color_space = models.CharField(max_length=50, blank=True)
    flash = models.CharField(max_length=100, blank=True)
    digital_zoom_ratio = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )

    # EXIF Location Data
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )
    altitude = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True
    )
    location_description = models.CharField(max_length=200, blank=True)

    # EXIF Time Data
    date_taken = models.DateTimeField(blank=True, null=True)
    date_modified = models.DateTimeField(blank=True, null=True)

    # Additional metadata
    software_used = models.CharField(max_length=100, blank=True)
    copyright = models.CharField(max_length=200, blank=True)

    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_taken", "-created_at"]
        verbose_name = "Photo"
        verbose_name_plural = "Photos"
        indexes = [
            models.Index(fields=["user", "-date_taken"]),
            models.Index(fields=["is_public", "-date_taken"]),
            models.Index(fields=["camera_make", "camera_model"]),
            models.Index(fields=["tags"]),
        ]

    def __str__(self):
        return f"{self.title or 'Untitled'} - {self.user.username}"

    def save(self, *args, **kwargs):
        """Override save to handle basic photo creation"""
        # Don't extract EXIF or generate thumbnail here - do it manually after file is saved
        super().save(*args, **kwargs)

    def extract_exif_data(self):
        """Extract EXIF data from the photo file"""
        try:
            if self.is_raw:
                self.extract_raw_exif()
            else:
                self.extract_jpeg_exif()
        except Exception as e:
            # Log error but don't fail the upload
            print(f"Error extracting EXIF data: {e}")

    def extract_jpeg_exif(self):
        """Extract EXIF data from JPEG/TIFF files"""
        try:
            with open(self.original_file.path, "rb") as f:
                tags = exifread.process_file(f)

            # Camera information
            if "Image Make" in tags:
                self.camera_make = str(tags["Image Make"])
            if "Image Model" in tags:
                self.camera_model = str(tags["Image Model"])
            if "EXIF LensMake" in tags:
                self.lens_make = str(tags["EXIF LensMake"])
            if "EXIF LensModel" in tags:
                self.lens_model = str(tags["EXIF LensModel"])

            # Focal length
            if "EXIF FocalLength" in tags:
                self.focal_length = float(tags["EXIF FocalLength"].values[0])
            if "EXIF FocalLengthIn35mmFilm" in tags:
                self.focal_length_35mm = int(
                    tags["EXIF FocalLengthIn35mmFilm"].values[0]
                )

            # Exposure settings
            if "EXIF ExposureTime" in tags:
                self.shutter_speed = str(tags["EXIF ExposureTime"])
            if "EXIF FNumber" in tags:
                self.aperture = float(tags["EXIF FNumber"].values[0])
            if "EXIF ISOSpeedRatings" in tags:
                self.iso = int(tags["EXIF ISOSpeedRatings"].values[0])
            if "EXIF ExposureBiasValue" in tags:
                self.exposure_bias = float(tags["EXIF ExposureBiasValue"].values[0])
            if "EXIF ExposureMode" in tags:
                self.exposure_mode = str(tags["EXIF ExposureMode"])
            if "EXIF MeteringMode" in tags:
                self.metering_mode = str(tags["EXIF MeteringMode"])

            # Image settings
            if "EXIF WhiteBalance" in tags:
                self.white_balance = str(tags["EXIF WhiteBalance"])
            if "EXIF ColorSpace" in tags:
                self.color_space = str(tags["EXIF ColorSpace"])
            if "EXIF Flash" in tags:
                self.flash = str(tags["EXIF Flash"])
            if "EXIF DigitalZoomRatio" in tags:
                self.digital_zoom_ratio = float(tags["EXIF DigitalZoomRatio"].values[0])

            # GPS coordinates
            if "GPS GPSLatitude" in tags and "GPS GPSLongitude" in tags:
                self.latitude = self.convert_gps_coordinate(
                    tags["GPS GPSLatitude"], tags["GPS GPSLatitudeRef"]
                )
                self.longitude = self.convert_gps_coordinate(
                    tags["GPS GPSLongitude"], tags["GPS GPSLongitudeRef"]
                )
            if "GPS GPSAltitude" in tags:
                self.altitude = float(tags["GPS GPSAltitude"].values[0])

            # Date information
            if "EXIF DateTimeOriginal" in tags:
                try:
                    date_str = str(tags["EXIF DateTimeOriginal"])
                    self.date_taken = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                except:
                    pass

            # Other metadata
            if "Image Software" in tags:
                self.software_used = str(tags["Image Software"])
            if "Image Copyright" in tags:
                self.copyright = str(tags["Image Copyright"])

        except Exception as e:
            print(f"Error extracting JPEG EXIF: {e}")

    def extract_raw_exif(self):
        """Extract EXIF data from RAW files using rawpy"""
        try:
            with rawpy.imread(self.original_file.path) as raw:
                # Get basic image info
                self.width = raw.sizes.width
                self.height = raw.sizes.height

                # Extract metadata
                metadata = raw.metadata
                if hasattr(metadata, "camera_make"):
                    self.camera_make = metadata.camera_make
                if hasattr(metadata, "camera_model"):
                    self.camera_model = metadata.camera_model
                if hasattr(metadata, "lens_make"):
                    self.lens_make = metadata.lens_make
                if hasattr(metadata, "lens_model"):
                    self.lens_model = metadata.lens_model

                # Extract other available metadata
                if hasattr(metadata, "focal_length"):
                    self.focal_length = metadata.focal_length
                if hasattr(metadata, "iso"):
                    self.iso = metadata.iso
                if hasattr(metadata, "shutter_speed"):
                    self.shutter_speed = str(metadata.shutter_speed)
                if hasattr(metadata, "aperture"):
                    self.aperture = metadata.aperture

        except Exception as e:
            print(f"Error extracting RAW EXIF: {e}")

    def convert_gps_coordinate(self, coord, ref):
        """Convert GPS coordinate from degrees/minutes/seconds to decimal"""
        try:
            degrees = float(coord.values[0].num) / float(coord.values[0].den)
            minutes = float(coord.values[1].num) / float(coord.values[1].den)
            seconds = float(coord.values[2].num) / float(coord.values[2].den)

            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

            if ref.values[0] in ["S", "W"]:
                decimal = -decimal

            return decimal
        except:
            return None

    def generate_thumbnail(self):
        """Generate a thumbnail for the photo"""
        try:
            if self.is_raw:
                # For RAW files, use rawpy to convert to PIL Image
                with rawpy.imread(self.original_file.path) as raw:
                    rgb = raw.postprocess()
                    img = Image.fromarray(rgb)
            else:
                # For regular images, open directly with PIL
                img = Image.open(self.original_file.path)

            # Convert to RGB if necessary
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            # Store original dimensions
            self.width = img.width
            self.height = img.height

            # Create thumbnail (max 300x300, maintain aspect ratio)
            img.thumbnail((450, 450), Image.Resampling.LANCZOS)

            # Save thumbnail to BytesIO
            thumb_io = BytesIO()
            img.save(thumb_io, format="JPEG", quality=85, optimize=True)
            thumb_io.seek(0)

            # Generate thumbnail filename
            thumb_name = f"thumb_{uuid.uuid4()}.jpg"
            thumb_path = os.path.join(
                "photos", str(self.user.id), "thumbnails", thumb_name
            )

            # Save thumbnail
            from django.core.files.base import ContentFile

            self.thumbnail.save(
                thumb_path, ContentFile(thumb_io.getvalue()), save=False
            )

        except Exception as e:
            print(f"Error generating thumbnail: {e}")

    def get_file_size_mb(self):
        """Return file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)

    def get_dimensions_display(self):
        """Return formatted dimensions"""
        if self.width and self.height:
            return f"{self.width} × {self.height}"
        return "Unknown"

    def get_exposure_display(self):
        """Return formatted exposure information"""
        parts = []
        if self.shutter_speed:
            parts.append(f"1/{self.shutter_speed}s")
        if self.aperture:
            parts.append(f"f/{self.aperture}")
        if self.iso:
            parts.append(f"ISO {self.iso}")
        return " • ".join(parts) if parts else "Unknown"

    def get_camera_display(self):
        """Return formatted camera information"""
        parts = []
        if self.camera_make:
            parts.append(self.camera_make)
        if self.camera_model:
            parts.append(self.camera_model)
        return " ".join(parts) if parts else "Unknown"

    def get_tags_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
        return []

    def delete(self, *args, **kwargs):
        """Override delete to remove files from storage"""
        # Delete original file
        if self.original_file:
            if os.path.isfile(self.original_file.path):
                os.remove(self.original_file.path)

        # Delete thumbnail
        if self.thumbnail:
            if os.path.isfile(self.thumbnail.path):
                os.remove(self.thumbnail.path)

        super().delete(*args, **kwargs)
