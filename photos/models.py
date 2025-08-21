import os
import uuid
from datetime import datetime
from django.db import models
from django.contrib.auth import get_user_model
from PIL import Image
import exifread
import rawpy
from io import BytesIO

COLLECTION_TYPES = [
    ("personal", "Personal"),
    ("shared", "Shared"),
    ("group", "Group"),
]

SORT_OPTIONS = [
    ("date_desc", "Newest First"),
    ("date_asc", "Oldest First"),
    ("alphabetical_asc", "A-Z"),
    ("alphabetical_desc", "Z-A"),
    ("random", "Random"),
    ("custom", "Custom"),
]

User = get_user_model()

# ===============================
# PHOTOS
# ===============================


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

    def get_tags_list(self):
        """Return tags as a list of strings, extracting hashtags"""
        if self.tags:
            # Extract hashtags: split by space and filter those starting with #
            hashtags = [tag.strip() for tag in self.tags.split() if tag.strip().startswith('#')]
            # Remove the # symbol and return clean tags
            return [tag[1:] for tag in hashtags]
        return []

    def set_tags_from_list(self, tag_list):
        """Set tags from a list, converting to hashtag format"""
        hashtags = [f"#{tag.strip()}" for tag in tag_list if tag.strip()]
        self.tags = " ".join(hashtags)
    
    def add_tag(self, tag):
        """Add a single tag to the photo"""
        if not tag.startswith('#'):
            tag = f"#{tag}"
        current_tags = self.tags.split() if self.tags else []
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = " ".join(current_tags)

    def remove_tag(self, tag):
        """Remove a single tag from the photo"""
        if not tag.startswith('#'):
            tag = f"#{tag}"
        
        current_tags = self.tags.split() if self.tags else []
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = " ".join(current_tags)
    
    def has_tag(self, tag):
        """Check if photo has a specific tag"""
        if not tag.startswith('#'):
            tag = f"#{tag}"
        return tag in (self.tags.split() if self.tags else [])

    def extract_exif_data(self):
        """Extract EXIF data from the photo file"""
        try:
            if self.is_raw:
                print(f"Extracting EXIF data from RAW file: {self.original_file.name}")
                self.extract_raw_exif()
            else:
                print(
                    f"Extracting EXIF data from JPEG/TIFF file: {self.original_file.name}"
                )
                self.extract_jpeg_exif()

            # Ensure we have basic dimensions
            if not self.width or not self.height:
                print(f"Warning: No dimensions extracted for {self.original_file.name}")

        except Exception as e:
            # Log error but don't fail the upload
            print(f"Error extracting EXIF data from {self.original_file.name}: {e}")
            import traceback

            traceback.print_exc()

            # Try to extract at least basic dimensions as fallback
            try:
                if self.is_raw:
                    with rawpy.imread(self.original_file.path) as raw:
                        self.width = raw.sizes.width
                        self.height = raw.sizes.height
                else:
                    with Image.open(self.original_file.path) as img:
                        self.width = img.width
                        self.height = img.height
                print(
                    f"Extracted basic dimensions as fallback: {self.width}x{self.height}"
                )
            except Exception as dim_error:
                print(f"Could not extract even basic dimensions: {dim_error}")

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
                # Convert decimal to fraction for shutter speed
                exposure_time = tags["EXIF ExposureTime"]
                if hasattr(exposure_time, "values") and len(exposure_time.values) > 0:
                    exposure_value = exposure_time.values[0]
                    if hasattr(exposure_value, "num") and hasattr(
                        exposure_value, "den"
                    ):
                        # Already in fraction format
                        self.shutter_speed = (
                            f"{exposure_value.num}/{exposure_value.den}"
                        )
                    else:
                        # Convert decimal to fraction if needed
                        try:
                            decimal_value = float(exposure_value)
                            if decimal_value < 1:
                                fraction = 1 / decimal_value
                                if fraction > 1:
                                    self.shutter_speed = f"1/{int(round(fraction))}"
                                else:
                                    self.shutter_speed = str(decimal_value)
                            else:
                                self.shutter_speed = str(decimal_value)
                        except:
                            self.shutter_speed = str(exposure_time)
                else:
                    self.shutter_speed = str(exposure_time)
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

            # Enhanced EXIF extraction using exiftool for better white balance and color temperature
            print("Attempting enhanced EXIF extraction with exiftool for JPEG...")
            if self.extract_exif_with_exiftool():
                print("Successfully enhanced JPEG EXIF data using exiftool")
            else:
                print("exiftool enhancement not available, using exifread data only")

        except Exception as e:
            print(f"Error extracting JPEG EXIF: {e}")

    def extract_raw_exif(self):
        """Extract EXIF data from RAW files using multiple methods for better compatibility"""
        try:
            with rawpy.imread(self.original_file.path) as raw:
                # Get basic image info first
                self.width = raw.sizes.width
                self.height = raw.sizes.height
                print(f"Extracted dimensions: {self.width}x{self.height}")

                # Method 1: Try to get camera info from rawpy metadata
                try:
                    if hasattr(raw, "metadata") and raw.metadata:
                        metadata = raw.metadata
                    if hasattr(metadata, "camera_make") and metadata.camera_make:
                        self.camera_make = str(metadata.camera_make)
                        print(f"Found camera make via rawpy: {self.camera_make}")
                    if hasattr(metadata, "camera_model") and metadata.camera_model:
                        self.camera_model = str(metadata.camera_model)
                        print(f"Found camera model via rawpy: {self.camera_model}")
                    if hasattr(metadata, "lens_make") and metadata.lens_make:
                        self.lens_make = str(metadata.lens_make)
                    if hasattr(metadata, "lens_model") and metadata.lens_model:
                        self.lens_model = str(metadata.lens_model)
                except Exception as e:
                    print(f"rawpy metadata extraction failed: {e}")

                # Method 2: Try alternative rawpy attributes
                try:
                    if hasattr(raw, "camera_make") and raw.camera_make:
                        self.camera_make = str(raw.camera_make)
                        print(
                            f"Found camera make via rawpy attribute: {self.camera_make}"
                        )
                    if hasattr(raw, "camera_model") and raw.camera_model:
                        self.camera_model = str(raw.camera_model)
                        print(
                            f"Found camera model via rawpy attribute: {self.camera_model}"
                        )
                except Exception as e:
                    print(f"rawpy attribute extraction failed: {e}")

                # Method 3: Try to extract EXIF with exifread (most reliable for metadata)
                try:
                    print(
                        f"Attempting exifread extraction for {self.original_file.name}"
                    )
                    with open(self.original_file.path, "rb") as f:
                        tags = exifread.process_file(f)

                    print(f"exifread found {len(tags)} tags")

                    # Extract camera information from EXIF tags
                    if "Image Make" in tags:
                        self.camera_make = str(tags["Image Make"])
                        print(f"Found camera make via exifread: {self.camera_make}")
                    if "Image Model" in tags:
                        self.camera_model = str(tags["Image Model"])
                        print(f"Found camera model via exifread: {self.camera_model}")
                    if "EXIF LensMake" in tags:
                        self.lens_make = str(tags["EXIF LensMake"])
                    if "EXIF LensModel" in tags:
                        self.lens_model = str(tags["EXIF LensModel"])

                    # Extract focal length
                    if "EXIF FocalLength" in tags:
                        try:
                            self.focal_length = float(
                                tags["EXIF FocalLength"].values[0]
                            )
                            print(f"Found focal length: {self.focal_length}")
                        except (ValueError, TypeError, IndexError):
                            pass

                    if "EXIF FocalLengthIn35mmFilm" in tags:
                        try:
                            self.focal_length_35mm = int(
                                tags["EXIF FocalLengthIn35mmFilm"].values[0]
                            )
                            print(f"Found focal length 35mm: {self.focal_length_35mm}")
                        except (ValueError, TypeError, IndexError):
                            pass

                    # Extract exposure settings
                    if "EXIF ExposureTime" in tags:
                        self.shutter_speed = str(tags["EXIF ExposureTime"])
                        print(f"Found shutter speed: {self.shutter_speed}")
                    if "EXIF FNumber" in tags:
                        try:
                            self.aperture = float(tags["EXIF FNumber"].values[0])
                            print(f"Found aperture: {self.aperture}")
                        except (ValueError, TypeError, IndexError):
                            pass
                    if "EXIF ISOSpeedRatings" in tags:
                        try:
                            self.iso = int(tags["EXIF ISOSpeedRatings"].values[0])
                            print(f"Found ISO: {self.iso}")
                        except (ValueError, TypeError, IndexError):
                            pass

                    # Extract additional data
                    if "EXIF ExposureBiasValue" in tags:
                        try:
                            self.exposure_bias = float(
                                tags["EXIF ExposureBiasValue"].values[0]
                            )
                        except (ValueError, TypeError, IndexError):
                            pass

                    if "EXIF ExposureMode" in tags:
                        self.exposure_mode = str(tags["EXIF ExposureMode"])
                    if "EXIF MeteringMode" in tags:
                        self.metering_mode = str(tags["EXIF MeteringMode"])
                    if "EXIF WhiteBalance" in tags:
                        self.white_balance = str(tags["EXIF WhiteBalance"])
                    if "EXIF ColorSpace" in tags:
                        self.color_space = str(tags["EXIF ColorSpace"])
                    if "EXIF Flash" in tags:
                        self.flash = str(tags["EXIF Flash"])
                    if "EXIF DigitalZoomRatio" in tags:
                        try:
                            self.digital_zoom_ratio = float(
                                tags["EXIF DigitalZoomRatio"].values[0]
                            )
                        except (ValueError, TypeError, IndexError):
                            pass

                    # GPS coordinates
                    if "GPS GPSLatitude" in tags and "GPS GPSLongitude" in tags:
                        try:
                            self.latitude = self.convert_gps_coordinate(
                                tags["GPS GPSLatitude"], tags["GPS GPSLatitudeRef"]
                            )
                            self.longitude = self.convert_gps_coordinate(
                                tags["GPS GPSLongitude"], tags["GPS GPSLongitudeRef"]
                            )
                            print(
                                f"Found GPS coordinates: {self.latitude}, {self.longitude}"
                            )
                        except:
                            pass

                    if "GPS GPSAltitude" in tags:
                        try:
                            self.altitude = float(tags["GPS GPSAltitude"].values[0])
                        except (ValueError, TypeError, IndexError):
                            pass

                    # Date information
                    if "EXIF DateTimeOriginal" in tags:
                        try:
                            date_str = str(tags["EXIF DateTimeOriginal"])
                            self.date_taken = datetime.strptime(
                                date_str, "%Y:%m:%d %H:%M:%S"
                            )
                            print(f"Found date taken: {self.date_taken}")
                        except:
                            pass

                    # Other metadata
                    if "Image Software" in tags:
                        self.software_used = str(tags["Image Software"])
                    if "Image Copyright" in tags:
                        self.copyright = str(tags["Image Copyright"])

                except Exception as e:
                    print(f"exifread extraction failed: {e}")
                    import traceback

                    traceback.print_exc()

                # Method 4: Try exiftool as fallback if exifread failed
                if not self.camera_make and not self.camera_model:
                    print("exifread failed, trying exiftool as fallback...")
                    if self.extract_exif_with_exiftool():
                        print("Successfully extracted EXIF data using exiftool")
                    else:
                        print("exiftool also failed, no EXIF data extracted")

                # Method 5: Try to get basic info from rawpy if all EXIF methods failed
                if not self.camera_make and not self.camera_model:
                    try:
                        # Some RAW files store basic info in different rawpy attributes
                        if hasattr(raw, "color_desc"):
                            print(f"Color description: {raw.color_desc}")
                        if hasattr(raw, "num_colors"):
                            print(f"Number of colors: {raw.num_colors}")
                        if hasattr(raw, "white_level"):
                            print(f"White level: {raw.white_level}")
                    except Exception as e:
                        print(f"Additional rawpy info extraction failed: {e}")

        except Exception as e:
            print(f"Error extracting RAW EXIF: {e}")
            import traceback

            traceback.print_exc()
            # Set basic dimensions if possible
            try:
                with rawpy.imread(self.original_file.path) as raw:
                    self.width = raw.sizes.width
                    self.height = raw.sizes.height
                    print(
                        f"Extracted basic dimensions as fallback: {self.width}x{self.height}"
                    )
            except Exception as dim_error:
                print(f"Could not extract even basic dimensions: {dim_error}")

    def extract_exif_with_exiftool(self):
        """Alternative EXIF extraction using exiftool for problematic RAW files"""
        try:
            import subprocess
            import json

            # Check if exiftool is available
            try:
                result = subprocess.run(
                    ["exiftool", "-ver"], capture_output=True, text=True, timeout=10
                )
                if result.returncode != 0:
                    print("exiftool not available, skipping exiftool extraction")
                    return False
                print(f"exiftool version {result.stdout.strip()} found")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print("exiftool not found, skipping exiftool extraction")
                return False

            # Extract EXIF data using exiftool with JSON output
            cmd = [
                "exiftool",
                "-json",
                "-n",  # Numeric output
                "-q",  # Quiet mode
                self.original_file.path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and result.stdout:
                try:
                    data = json.loads(result.stdout)
                    if data and len(data) > 0:
                        exif_data = data[0]
                        print(f"exiftool extracted {len(exif_data)} fields")

                        # Extract camera information
                        if "Make" in exif_data:
                            self.camera_make = str(exif_data["Make"])
                            print(f"Found camera make via exiftool: {self.camera_make}")
                        if "Model" in exif_data:
                            self.camera_model = str(exif_data["Model"])
                            print(
                                f"Found camera model via exiftool: {self.camera_model}"
                            )
                        if "LensMake" in exif_data:
                            self.lens_make = str(exif_data["LensMake"])
                        if "LensModel" in exif_data:
                            self.lens_model = str(exif_data["LensModel"])

                        # Extract focal length
                        if "FocalLength" in exif_data:
                            try:
                                self.focal_length = float(exif_data["FocalLength"])
                                print(
                                    f"Found focal length via exiftool: {self.focal_length}"
                                )
                            except (ValueError, TypeError):
                                pass
                        if "FocalLengthIn35mmFormat" in exif_data:
                            try:
                                self.focal_length_35mm = int(
                                    exif_data["FocalLengthIn35mmFormat"]
                                )
                                print(
                                    f"Found focal length 35mm via exiftool: {self.focal_length_35mm}"
                                )
                            except (ValueError, TypeError):
                                pass

                        # Extract exposure settings
                        if "ExposureTime" in exif_data:
                            # Convert decimal to fraction for shutter speed
                            exposure_time = exif_data["ExposureTime"]
                            if (
                                isinstance(exposure_time, (int, float))
                                and exposure_time < 1
                            ):
                                # Convert decimal to fraction (e.g., 0.008 -> "1/125")
                                try:
                                    fraction = 1 / exposure_time
                                    if fraction > 1:
                                        self.shutter_speed = f"1/{int(round(fraction))}"
                                    else:
                                        self.shutter_speed = str(exposure_time)
                                except:
                                    self.shutter_speed = str(exposure_time)
                            else:
                                self.shutter_speed = str(exposure_time)
                            print(
                                f"Found shutter speed via exiftool: {self.shutter_speed}"
                            )
                        if "FNumber" in exif_data:
                            try:
                                self.aperture = float(exif_data["FNumber"])
                                print(f"Found aperture via exiftool: {self.aperture}")
                            except (ValueError, TypeError):
                                pass
                        if "ISO" in exif_data:
                            try:
                                self.iso = int(exif_data["ISO"])
                                print(f"Found ISO via exiftool: {self.iso}")
                            except (ValueError, TypeError):
                                pass

                        # Extract additional data
                        if "ExposureBiasValue" in exif_data:
                            try:
                                self.exposure_bias = float(
                                    exif_data["ExposureBiasValue"]
                                )
                                print(
                                    f"Found exposure bias via exiftool: {self.exposure_bias}"
                                )
                            except (ValueError, TypeError):
                                pass
                        if "ExposureMode" in exif_data:
                            # Convert numeric exposure mode to readable text
                            exposure_mode = exif_data["ExposureMode"]
                            if isinstance(exposure_mode, (int, str)):
                                mode_text = self.convert_exposure_mode(exposure_mode)
                                self.exposure_mode = mode_text
                                print(
                                    f"Found exposure mode via exiftool: {self.exposure_mode}"
                                )
                        elif "ExposureProgram" in exif_data:
                            # Fallback for exposure mode
                            program = exif_data["ExposureProgram"]
                            if isinstance(program, (int, str)):
                                mode_text = self.convert_exposure_program(program)
                                self.exposure_mode = mode_text
                                print(
                                    f"Found exposure program via exiftool: {self.exposure_mode}"
                                )

                        if "MeteringMode" in exif_data:
                            # Convert numeric metering mode to readable text
                            metering_mode = exif_data["MeteringMode"]
                            if isinstance(metering_mode, (int, str)):
                                mode_text = self.convert_metering_mode(metering_mode)
                                self.metering_mode = mode_text
                                print(
                                    f"Found metering mode via exiftool: {self.metering_mode}"
                                )

                        if "WhiteBalance" in exif_data:
                            # Check if we have actual color temperature first
                            if "ColorTempAsShot" in exif_data:
                                color_temp = exif_data["ColorTempAsShot"]
                                if (
                                    isinstance(color_temp, (int, float))
                                    and color_temp > 0
                                ):
                                    self.white_balance = f"{int(color_temp)}K"
                                    print(
                                        f"Found white balance via exiftool: {self.white_balance} (ColorTempAsShot)"
                                    )
                                else:
                                    # Fallback to numeric conversion
                                    white_balance = exif_data["WhiteBalance"]
                                    if isinstance(white_balance, (int, str)):
                                        wb_text = self.convert_white_balance(
                                            white_balance
                                        )
                                        self.white_balance = wb_text
                                        print(
                                            f"Found white balance via exiftool: {self.white_balance}"
                                        )
                            else:
                                # Convert numeric white balance to readable text
                                white_balance = exif_data["WhiteBalance"]
                                if isinstance(white_balance, (int, str)):
                                    wb_text = self.convert_white_balance(white_balance)
                                    self.white_balance = wb_text
                                    print(
                                        f"Found white balance via exiftool: {self.white_balance}"
                                    )
                        elif "WhiteBalanceMode" in exif_data:
                            # Fallback for white balance
                            wb_mode = exif_data["WhiteBalanceMode"]
                            if isinstance(wb_mode, (int, str)):
                                wb_text = self.convert_white_balance(wb_mode)
                                self.white_balance = wb_text
                                print(
                                    f"Found white balance via exiftool: {self.white_balance}"
                                )

                        if "ColorSpace" in exif_data:
                            # Convert numeric color space to readable text
                            color_space = exif_data["ColorSpace"]
                            if isinstance(color_space, (int, str)):
                                cs_text = self.convert_color_space(color_space)
                                self.color_space = cs_text
                                print(
                                    f"Found color space via exiftool: {self.color_space}"
                                )

                        if "Flash" in exif_data:
                            # Convert numeric flash to readable text
                            flash = exif_data["Flash"]
                            if isinstance(flash, (int, str)):
                                flash_text = self.convert_flash(flash)
                                self.flash = flash_text
                                print(f"Found flash via exiftool: {self.flash}")
                        elif "FlashMode" in exif_data:
                            # Fallback for flash
                            flash_mode = exif_data["FlashMode"]
                            if isinstance(flash_mode, (int, str)):
                                flash_text = self.convert_flash(flash_mode)
                                self.flash = flash_text
                                print(f"Found flash mode via exiftool: {self.flash}")

                        if "DigitalZoomRatio" in exif_data:
                            try:
                                self.digital_zoom_ratio = float(
                                    exif_data["DigitalZoomRatio"]
                                )
                                print(
                                    f"Found digital zoom via exiftool: {self.digital_zoom_ratio}"
                                )
                            except (ValueError, TypeError):
                                pass

                        # GPS coordinates
                        if "GPSLatitude" in exif_data and "GPSLongitude" in exif_data:
                            try:
                                self.latitude = float(exif_data["GPSLatitude"])
                                self.longitude = float(exif_data["GPSLongitude"])
                                print(
                                    f"Found GPS coordinates via exiftool: {self.latitude}, {self.longitude}"
                                )
                            except (ValueError, TypeError):
                                pass

                        if "GPSAltitude" in exif_data:
                            try:
                                self.altitude = float(exif_data["GPSAltitude"])
                            except (ValueError, TypeError):
                                pass

                        # Date information
                        if "DateTimeOriginal" in exif_data:
                            try:
                                date_str = str(exif_data["DateTimeOriginal"])
                                # Try different date formats
                                for fmt in [
                                    "%Y:%m:%d %H:%M:%S",
                                    "%Y-%m-%d %H:%M:%S",
                                    "%Y:%m:%d %H:%M:%S%z",
                                ]:
                                    try:
                                        self.date_taken = datetime.strptime(
                                            date_str, fmt
                                        )
                                        print(
                                            f"Found date taken via exiftool: {self.date_taken}"
                                        )
                                        break
                                    except ValueError:
                                        continue
                            except:
                                pass

                        # Other metadata
                        if "Software" in exif_data:
                            self.software_used = str(exif_data["Software"])
                            print(f"Found software via exiftool: {self.software_used}")
                        elif "ProcessingSoftware" in exif_data:
                            # Fallback for software
                            self.software_used = str(exif_data["ProcessingSoftware"])
                            print(
                                f"Found processing software via exiftool: {self.software_used}"
                            )

                        if "Copyright" in exif_data:
                            self.copyright = str(exif_data["Copyright"])
                            print(f"Found copyright via exiftool: {self.copyright}")

                        # Set default values for empty fields to match JPEG behavior
                        if not self.exposure_mode:
                            self.exposure_mode = "Auto Exposure"
                        if not self.metering_mode:
                            self.metering_mode = "Pattern"
                        if not self.white_balance:
                            self.white_balance = "Auto"
                        if not self.color_space:
                            self.color_space = "sRGB"
                        if not self.flash:
                            self.flash = "Flash did not fire"
                        if not self.software_used:
                            self.software_used = "Unknown"
                        if not self.copyright:
                            self.copyright = ""

                        print(
                            f"Completed exiftool extraction with {len(exif_data)} fields"
                        )
                        return True

                except json.JSONDecodeError as e:
                    print(f"Failed to parse exiftool JSON output: {e}")
                    return False
            else:
                print(f"exiftool failed with return code {result.returncode}")
                if result.stderr:
                    print(f"exiftool stderr: {result.stderr}")
                return False

        except Exception as e:
            print(f"exiftool extraction failed: {e}")
            return False

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

                    # Store dimensions if not already set (should be set in extract_raw_exif)
                    if not self.width or not self.height:
                        self.width = raw.sizes.width
                        self.height = raw.sizes.height
            else:
                # For regular images, open directly with PIL
                img = Image.open(self.original_file.path)

                # Store dimensions if not already set (should be set in extract_jpeg_exif)
                if not self.width or not self.height:
                    self.width = img.width
                    self.height = img.height

            # Convert to RGB if necessary
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            # Create thumbnail (max 450x450, maintain aspect ratio)
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
            # Try to set basic dimensions as fallback
            if not self.width or not self.height:
                try:
                    if self.is_raw:
                        with rawpy.imread(self.original_file.path) as raw:
                            self.width = raw.sizes.width
                            self.height = raw.sizes.height
                    else:
                        with Image.open(self.original_file.path) as img:
                            self.width = img.width
                            self.height = img.height
                except Exception as dim_error:
                    print(f"Could not extract dimensions: {dim_error}")

    def validate_photo_processing(self):
        """Validate that the photo was processed correctly"""
        validation_errors = []

        # Check if we have basic dimensions
        if not self.width or not self.height:
            validation_errors.append("Photo dimensions not extracted")

        # Check if thumbnail was generated
        if not self.thumbnail:
            validation_errors.append("Thumbnail not generated")

        # Check if we have at least some basic metadata
        if not any(
            [
                self.camera_make,
                self.camera_model,
                self.iso,
                self.aperture,
                self.shutter_speed,
            ]
        ):
            validation_errors.append("No basic EXIF metadata extracted")

        return validation_errors

    def get_processing_status(self):
        """Get a summary of the photo processing status"""
        status = {
            "has_dimensions": bool(self.width and self.height),
            "has_thumbnail": bool(self.thumbnail),
            "has_camera_info": bool(self.camera_make or self.camera_model),
            "has_exposure_info": bool(self.iso or self.aperture or self.shutter_speed),
            "has_location": bool(self.latitude and self.longitude),
            "has_date": bool(self.date_taken),
        }
        return status

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
            parts.append(f"{self.shutter_speed}s")
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

    def convert_exposure_mode(self, mode_value):
        """Convert numeric exposure mode to readable text"""
        mode_map = {
            0: "Auto Exposure",
            1: "Manual",
            2: "Auto",
            3: "Auto (P)",
            4: "Auto (A)",
            5: "Auto (S)",
            6: "Auto (M)",
            7: "Auto (Program)",
            8: "Auto (Aperture Priority)",
            9: "Auto (Shutter Priority)",
            10: "Auto (Manual)",
        }
        return mode_map.get(int(mode_value), f"Mode {mode_value}")

    def convert_exposure_program(self, program_value):
        """Convert numeric exposure program to readable text"""
        program_map = {
            0: "Not Defined",
            1: "Manual",
            2: "Program AE",
            3: "Aperture Priority AE",
            4: "Shutter Priority AE",
            5: "Creative Program",
            6: "Action Program",
            7: "Portrait Mode",
            8: "Landscape Mode",
        }
        return program_map.get(int(program_value), f"Program {program_value}")

    def convert_metering_mode(self, mode_value):
        """Convert numeric metering mode to readable text"""
        mode_map = {
            0: "Unknown",
            1: "Average",
            2: "Center Weighted Average",
            3: "Pattern",
            4: "Spot",
            5: "Multi-Spot",
            6: "Multi-Segment",
            7: "Partial",
            8: "Other",
        }
        return mode_map.get(int(mode_value), f"Metering {mode_value}")

    def convert_white_balance(self, wb_value):
        """Convert numeric white balance to readable text"""
        # Canon EOS specific white balance values
        wb_map = {
            0: "Auto",
            1: "Manual",
            2: "Daylight",
            3: "Cloudy",
            4: "Tungsten",
            5: "Fluorescent",
            6: "Flash",
            7: "Custom",
            8: "Shade",
            9: "Kelvin",  # This will be overridden by ColorTempAsShot if available
        }
        return wb_map.get(int(wb_value), f"WB {wb_value}")

    def convert_color_space(self, cs_value):
        """Convert numeric color space to readable text"""
        cs_map = {
            1: "sRGB",
            2: "Adobe RGB",
            3: "Wide Gamut RGB",
            4: "ProPhoto RGB",
            5: "DCI-P3",
            6: "Apple RGB",
        }
        return cs_map.get(int(cs_value), f"Color Space {cs_value}")

    def convert_flash(self, flash_value):
        """Convert numeric flash to readable text"""
        flash_map = {
            0: "Flash did not fire",
            1: "Flash fired",
            2: "Flash fired, return not detected",
            3: "Flash fired, return detected",
            4: "Flash fired, compulsory flash mode",
            5: "Flash fired, compulsory flash mode, return not detected",
            6: "Flash fired, compulsory flash mode, return detected",
            7: "Flash fired, auto mode",
            8: "Flash fired, auto mode, return not detected",
            9: "Flash fired, auto mode, return detected",
        }
        return flash_map.get(int(flash_value), f"Flash {flash_value}")

# ===============================
# COLLECTIONS
# ===============================
class Collection(models.Model):
    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
   
    # Owner and permissions
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="collections")
    collaborators = models.ManyToManyField(User, blank=True, related_name="collaborated_collections")
    is_public = models.BooleanField(default=False)

    # Collection metadata
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    cover_photo = models.ForeignKey(Photo, on_delete=models.SET_NULL, null=True, blank=True, related_name="collection_cover")
    collection_type = models.CharField(max_length=50, choices=COLLECTION_TYPES, default="personal")

    # Photos relationship
    photos = models.ManyToManyField(Photo, through="CollectionPhoto", related_name="collections")

    # Sorting and display
    sort_order = models.CharField(max_length=20, choices=SORT_OPTIONS, default="date_desc")
    custom_order = models.JSONField(default=list, blank=True)

    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "-updated_at"]),
            models.Index(fields=["-is_public", "-updated_at"]),
            models.Index(fields=["tags"]),
        ]
        verbose_name = "Collection"
        verbose_name_plural = "Collections"

    def __str__(self):
        return f"{self.name} - {self.owner.username}"

    def get_photo_count(self):
        """Return the number of photos in the collection"""
        return self.photos.count()

    def get_total_size_mb(self):
        """Return the total size of the collection in MB"""
        total_bytes = sum(photo.file_size for photo in self.photos.all())
        return round(total_bytes / (1024 * 1024), 2)

    def get_cover_photo_url(self):
        """Return the URL of the cover photo if it exists, else return the URL of the first photo"""
        if self.cover_photo and self.cover_photo.thumbnail:
            return self.cover_photo.thumbnail.url
        elif self.photos.exists():
            # Use first photo as cover if no cover photo is set
            first_photo = self.photos.first()
            return first_photo.thumbnail.url if first_photo.thumbnail else first_photo.original_file.url
        return None
    
    def get_tags_list(self):
        """Return tags as a list of strings, extracting hashtags"""
        if self.tags:
            # Extract hashtags: split by space and filter those starting with #
            hashtags = [tag.strip() for tag in self.tags.split() if tag.strip().startswith('#')]
            # Remove the # symbol and return clean tags
            return [tag[1:] for tag in hashtags]
        return []
    
    def set_tags_from_list(self, tag_list):
        """Set tags from a list, converting to hashtag format"""
        hashtags = [f"#{tag.strip()}" for tag in tag_list if tag.strip()]
        self.tags = " ".join(hashtags)
    
    def add_tag(self, tag):
        """Add a single tag to the collection"""
        if not tag.startswith('#'):
            tag = f"#{tag}"
        
        current_tags = self.tags.split() if self.tags else []
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = " ".join(current_tags)
    
    def remove_tag(self, tag):
        """Remove a tag from the collection"""
        if not tag.startswith('#'):
            tag = f"#{tag}"
        
        current_tags = self.tags.split() if self.tags else []
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = " ".join(current_tags)
    
    def has_tag(self, tag):
        """Check if collection has a specific tag"""
        if not tag.startswith('#'):
            tag = f"#{tag}"
        return tag in (self.tags.split() if self.tags else [])

    def get_collaborators_list(self):
        """Return collaborators as a list of usernames"""
        return [collaborator.username for collaborator in self.collaborators.all()]
    
    def get_collaborators_count(self):
        """Return the number of collaborators"""
        return self.collaborators.count()
    
    def add_photo(self, photo, order=None):
        """Add a photo to the collection"""
        if order is None:
            order = self.get_photo_count()

        CollectionPhoto.objects.create(
            collection=self,
            photo=photo,
            order=order
        )
        
    def remove_photo(self, photo):
        """Remove a photo from the collection"""
        CollectionPhoto.objects.filter(collection=self, photo=photo).delete()

    def reorder_photos(self, photo_order):
        """Reorder photos in the collection"""
        for index, photo_id in enumerate(photo_order):
            CollectionPhoto.objects.filter(
                collection=self,
                photo_id=photo_id
            ).update(order=index)
        
        

class CollectionPhoto(models.Model):
    """Intermediate model for managing photos in collections with ordering"""
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="collection_photos")
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="collection_photos")
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["order", "added_at"]
        unique_together = ["collection", "photo"]
        verbose_name = "Collection Photo"
        verbose_name_plural = "Collection Photos"
    
    def __str__(self):
        return f"{self.photo.title} in {self.collection.name}"
