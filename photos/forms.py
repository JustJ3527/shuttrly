from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Photo
import os

User = get_user_model()


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class PhotoUploadForm(forms.Form):
    """Form for uploading multiple photos including RAW files"""

    photos = forms.FileField(
        widget=MultipleFileInput(
            attrs={
                "multiple": True,
                "accept": ".jpg,.jpeg,.png,.tiff,.tif,.raw,.cr2,.cr3,.nef,.arw,.dng,.raf,.orf,.pef,.srw,.x3f,.rw2,.mrw,.crw,.kdc,.dcr,.mos,.mef,.nrw",
                "class": "form-control",
                "id": "photo-upload-input",
            }
        ),
        label=_("Select Photos"),
        help_text=_(
            "You can select multiple photos. Supported formats: JPEG, PNG, TIFF, RAW (CR2, NEF, ARW, DNG, etc.)"
        ),
    )

    title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Photo title (optional)")}
        ),
        label=_("Title"),
    )

    description = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Photo description (optional)"),
            }
        ),
        label=_("Description"),
    )

    tags = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Tags separated by commas (optional)"),
            }
        ),
        label=_("Tags"),
        help_text=_("Separate tags with commas"),
    )

    is_public = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Make this photo public"),
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.uploaded_photos = []

    def clean_photos(self):
        """Validate uploaded photos"""
        photos = self.files.getlist("photos")

        if not photos:
            raise ValidationError(_("Please select at least one photo to upload."))

        # Check file count limit (optional)
        if len(photos) > 50:
            raise ValidationError(_("You can upload a maximum of 50 photos at once."))

        # Validate each file
        for photo in photos:
            self.validate_single_photo(photo)

        return photos

    def validate_single_photo(self, photo):
        """Validate a single photo file"""
        # Check file size
        if photo.size > 100 * 1024 * 1024:  # 100MB limit
            raise ValidationError(
                _('File "%(filename)s" is too large. Maximum size is 100MB.'),
                params={"filename": photo.name},
            )

        # Check file extension
        ext = os.path.splitext(photo.name)[1].lower().lstrip(".")
        allowed_extensions = [
            "jpg",
            "jpeg",
            "png",
            "tiff",
            "tif",
            "raw",
            "cr2",
            "cr3",
            "nef",
            "arw",
            "dng",
            "raf",
            "orf",
            "pef",
            "srw",
            "x3f",
            "rw2",
            "mrw",
            "crw",
            "kdc",
            "dcr",
            "mos",
            "mef",
            "nrw",
        ]

        if ext not in allowed_extensions:
            raise ValidationError(
                _(
                    'File "%(filename)s" has an unsupported format. Allowed formats: %(allowed_formats)s'
                ),
                params={
                    "filename": photo.name,
                    "allowed_formats": ", ".join(allowed_extensions),
                },
            )

    def save_photos(self):
        """Save all uploaded photos"""
        photos = self.cleaned_data["photos"]
        saved_photos = []

        for photo_file in photos:
            # Determine if it's a RAW file
            ext = os.path.splitext(photo_file.name)[1].lower().lstrip(".")
            raw_extensions = [
                "raw",
                "cr2",
                "cr3",
                "nef",
                "arw",
                "dng",
                "raf",
                "orf",
                "pef",
                "srw",
                "x3f",
                "rw2",
                "mrw",
                "crw",
                "kdc",
                "dcr",
                "mos",
                "mef",
                "nrw",
            ]
            is_raw = ext in raw_extensions

            # Create Photo instance
            photo = Photo(
                user=self.user,
                original_file=photo_file,
                file_size=photo_file.size,
                file_extension=ext,
                is_raw=is_raw,
                title=self.cleaned_data.get("title", ""),
                description=self.cleaned_data.get("description", ""),
                tags=self.cleaned_data.get("tags", ""),
                is_public=self.cleaned_data.get("is_public", False),
            )

            # Save the photo (this will trigger EXIF extraction and thumbnail generation)
            photo.save()
            saved_photos.append(photo)

        return saved_photos


class PhotoEditForm(forms.ModelForm):
    """Form for editing photo metadata"""

    class Meta:
        model = Photo
        fields = ["title", "description", "tags", "is_public", "is_featured"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Photo title")}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Photo description"),
                }
            ),
            "tags": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Tags separated by commas"),
                }
            ),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "title": _("Title"),
            "description": _("Description"),
            "tags": _("Tags"),
            "is_public": _("Public"),
            "is_featured": _("Featured"),
        }
        help_texts = {
            "tags": _("Separate tags with commas"),
            "is_public": _("Make this photo visible to everyone"),
            "is_featured": _("Mark this photo as featured"),
        }


class PhotoSearchForm(forms.Form):
    """Form for searching and filtering photos"""

    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Search photos...")}
        ),
        label=_("Search"),
    )

    camera_make = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Camera brand")}
        ),
        label=_("Camera Brand"),
    )

    camera_model = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Camera model")}
        ),
        label=_("Camera Model"),
    )

    lens_model = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Lens model")}
        ),
        label=_("Lens"),
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label=_("From Date"),
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label=_("To Date"),
    )

    tags = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Tags (comma-separated)")}
        ),
        label=_("Tags"),
    )

    is_raw = forms.ChoiceField(
        choices=[
            ("", _("All formats")),
            ("true", _("RAW only")),
            ("false", _("Processed only")),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label=_("Format"),
    )

    sort_by = forms.ChoiceField(
        choices=[
            ("-date_taken", _("Date taken (newest first)")),
            ("date_taken", _("Date taken (oldest first)")),
            ("-created_at", _("Upload date (newest first)")),
            ("created_at", _("Upload date (oldest first)")),
            ("title", _("Title A-Z")),
            ("-title", _("Title Z-A")),
            ("-file_size", _("File size (largest first)")),
            ("file_size", _("File size (smallest first)")),
        ],
        required=False,
        initial="-date_taken",
        widget=forms.Select(attrs={"class": "form-control"}),
        label=_("Sort by"),
    )
