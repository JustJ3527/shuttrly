import os
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from .models import Photo
from .forms import PhotoUploadForm, PhotoEditForm, PhotoSearchForm


@login_required
def photo_upload(request):
    """Handle photo upload with batch processing"""
    if request.method == "POST":
        try:
            # Get uploaded files
            photos = request.FILES.getlist("photos")
            if not photos:
                messages.error(request, "Please select at least one photo to upload.")
                return redirect("photos:upload")

            # Get form data
            title = request.POST.get("title", "")
            description = request.POST.get("description", "")
            tags = request.POST.get("tags", "")
            is_public = request.POST.get("is_public") == "on"

            # Ensure media directory exists
            media_root = getattr(settings, "MEDIA_ROOT", "media")
            photos_dir = os.path.join(media_root, "photos", str(request.user.id))
            os.makedirs(photos_dir, exist_ok=True)
            os.makedirs(os.path.join(photos_dir, "thumbnails"), exist_ok=True)

            # Process photos in batches to avoid memory issues and timeouts
            batch_size = 15  # Process 15 photos at a time maximum
            total_photos = len(photos)
            uploaded_count = 0
            failed_count = 0
            processing_errors = []

            print(
                f"Starting upload of {total_photos} photos in batches of {batch_size}"
            )

            # Store session data for progress tracking
            request.session["upload_progress"] = {
                "total": total_photos,
                "processed": 0,
                "uploaded": 0,
                "failed": 0,
                "current_batch": 0,
                "status": "processing",
            }

            for batch_num in range(0, total_photos, batch_size):
                batch = photos[batch_num : batch_num + batch_size]
                current_batch_size = len(batch)

                # Update progress for current batch
                request.session["upload_progress"]["current_batch"] = (
                    batch_num // batch_size + 1
                )
                request.session.save()

                print(
                    f"Processing batch {batch_num // batch_size + 1}: {current_batch_size} photos"
                )

                for i, photo_file in enumerate(batch):
                    try:
                        print(
                            f"Processing photo {batch_num + i + 1}/{total_photos}: {photo_file.name}"
                        )

                        # Create Photo object
                        photo = Photo(
                            user=request.user,
                            original_file=photo_file,
                            title=title if title else "Untitled",
                            description=description if description else "",
                            tags=tags if tags else "",
                            is_public=is_public,
                            file_size=photo_file.size,
                            file_extension=photo_file.name.split(".")[-1].lower(),
                            is_raw=photo_file.name.lower().endswith(
                                (
                                    ".raw",
                                    ".cr2",
                                    ".cr3",
                                    ".nef",
                                    ".arw",
                                    ".dng",
                                    ".raf",
                                    ".orf",
                                    ".pef",
                                    ".srw",
                                    ".x3f",
                                    ".rw2",
                                    ".mrw",
                                    ".crw",
                                    ".kdc",
                                    ".dcr",
                                    ".mos",
                                    ".mef",
                                    ".nrw",
                                )
                            ),
                        )

                        # Save photo first to get the file path
                        photo.save()
                        print(f"Photo saved: {photo.id}")

                        # Now extract EXIF and generate thumbnail after file is saved
                        try:
                            print(f"Extracting EXIF for {photo_file.name}")
                            photo.extract_exif_data()
                            print(f"Generating thumbnail for {photo_file.name}")
                            photo.generate_thumbnail()
                            photo.save()  # Save again with EXIF data and thumbnail
                            uploaded_count += 1
                            print(f"Photo {photo_file.name} processed successfully")
                        except Exception as e:
                            print(f"Error processing photo {photo_file.name}: {e}")
                            processing_errors.append(f"{photo_file.name}: {str(e)}")
                            failed_count += 1
                            # Continue with other photos even if one fails

                        # Update progress
                        request.session["upload_progress"]["processed"] += 1
                        request.session["upload_progress"]["uploaded"] = uploaded_count
                        request.session["upload_progress"]["failed"] = failed_count
                        request.session.save()

                    except Exception as e:
                        print(f"Error saving photo {photo_file.name}: {e}")
                        processing_errors.append(f"{photo_file.name}: {str(e)}")
                        failed_count += 1
                        # Update progress
                        request.session["upload_progress"]["processed"] += 1
                        request.session["upload_progress"]["failed"] = failed_count
                        request.session.save()
                        continue

                # Small delay between batches to prevent server overload
                import time

                print(f"Batch {batch_num // batch_size + 1} completed. Waiting 0.5s...")
                time.sleep(0.5)

            # Mark upload as complete
            request.session["upload_progress"]["status"] = "completed"
            request.session.save()

            print(
                f"Upload completed. Successfully uploaded: {uploaded_count}, Failed: {failed_count}"
            )

            # Show results
            if failed_count > 0:
                messages.warning(
                    request,
                    f"Uploaded {uploaded_count} photos successfully, {failed_count} failed to process completely.",
                )
                if processing_errors:
                    # Store errors in session for detailed view
                    request.session["upload_errors"] = processing_errors[
                        :10
                    ]  # Limit to first 10 errors
            else:
                messages.success(
                    request, f"Successfully uploaded {uploaded_count} photo(s)"
                )

            return redirect("photos:gallery")

        except Exception as e:
            print(f"Critical error during upload: {e}")
            import traceback

            traceback.print_exc()

            # Mark upload as failed
            request.session["upload_progress"]["status"] = "failed"
            request.session["upload_progress"]["error"] = str(e)
            request.session.save()

            messages.error(request, f"Error uploading photos: {str(e)}")
            return redirect("photos:upload")

    context = {
        "max_file_size": "100 MB",
        "max_files": 50,
        "supported_formats": "JPEG, PNG, TIFF, RAW (CR2, CR3, NEF, ARW, DNG, etc.)",
    }
    return render(request, "photos/upload.html", context)


@login_required
def photo_gallery(request):
    """Display user's photo gallery with search and filtering"""
    # Get search form data
    search_form = PhotoSearchForm(request.GET)

    # Start with user's photos
    photos = Photo.objects.filter(user=request.user)

    # Apply search filters
    if search_form.is_valid():
        query = search_form.cleaned_data.get("query")
        if query:
            photos = photos.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(tags__icontains=query)
                | Q(camera_make__icontains=query)
                | Q(camera_model__icontains=query)
                | Q(lens_model__icontains=query)
            )

        # Filter by camera
        camera_make = search_form.cleaned_data.get("camera_make")
        if camera_make:
            photos = photos.filter(camera_make__icontains=camera_make)

        camera_model = search_form.cleaned_data.get("camera_model")
        if camera_model:
            photos = photos.filter(camera_model__icontains=camera_model)

        lens_model = search_form.cleaned_data.get("lens_model")
        if lens_model:
            photos = photos.filter(lens_model__icontains=lens_model)

        # Filter by date range
        date_from = search_form.cleaned_data.get("date_from")
        if date_from:
            photos = photos.filter(date_taken__gte=date_from)

        date_to = search_form.cleaned_data.get("date_to")
        if date_to:
            photos = photos.filter(date_taken__lte=date_to)

        # Filter by tags
        tags = search_form.cleaned_data.get("tags")
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            for tag in tag_list:
                photos = photos.filter(tags__icontains=tag)

        # Filter by format
        is_raw = search_form.cleaned_data.get("is_raw")
        if is_raw == "true":
            photos = photos.filter(is_raw=True)
        elif is_raw == "false":
            photos = photos.filter(is_raw=False)

        # Sort photos
        sort_by = search_form.cleaned_data.get("sort_by") or "-date_taken"
        photos = photos.order_by(sort_by)

    # Pagination
    paginator = Paginator(photos, 24)  # 24 photos per page (6x4 grid)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get statistics
    total_photos = photos.count()
    raw_photos = photos.filter(is_raw=True).count()
    public_photos = photos.filter(is_public=True).count()

    # Get unique cameras and lenses for filter suggestions
    # Use all user photos for filter options, not filtered photos
    all_user_photos = Photo.objects.filter(user=request.user)
    cameras = list(
        all_user_photos.values_list("camera_make", flat=True)
        .distinct()
        .exclude(camera_make="")
        .exclude(camera_make__isnull=True)
    )
    lenses = list(
        all_user_photos.values_list("lens_model", flat=True)
        .distinct()
        .exclude(lens_model="")
        .exclude(lens_model__isnull=True)
    )

    # Debug: Print cameras list to console
    print(f"DEBUG: Cameras list: {cameras}")
    print(f"DEBUG: Cameras count: {len(cameras)}")

    context = {
        "page_obj": page_obj,
        "search_form": search_form,
        "total_photos": total_photos,
        "raw_photos": raw_photos,
        "public_photos": public_photos,
        "cameras": cameras,
        "lenses": lenses,
    }
    return render(request, "photos/gallery.html", context)


@login_required
def photo_detail(request, photo_id):
    """Display detailed view of a single photo with EXIF data"""
    photo = get_object_or_404(Photo, id=photo_id, user=request.user)

    # Get related photos (same camera, lens, or tags)
    related_photos = Photo.objects.filter(user=request.user).exclude(id=photo.id)

    # Find photos with similar characteristics
    similar_photos = []
    if photo.camera_model:
        similar_photos.extend(
            related_photos.filter(camera_model=photo.camera_model)[:3]
        )
    if photo.lens_model:
        similar_photos.extend(related_photos.filter(lens_model=photo.lens_model)[:3])
    if photo.tags:
        tag_list = photo.get_tags_list()
        for tag in tag_list[:3]:
            similar_photos.extend(related_photos.filter(tags__icontains=tag)[:2])

    # Remove duplicates and limit to 6 photos
    seen_ids = set()
    unique_similar = []
    for p in similar_photos:
        if p.id not in seen_ids and len(unique_similar) < 6:
            unique_similar.append(p)
            seen_ids.add(p.id)

    context = {
        "photo": photo,
        "similar_photos": unique_similar,
    }
    return render(request, "photos/detail.html", context)


@login_required
def photo_edit(request, photo_id):
    """Edit photo metadata"""
    photo = get_object_or_404(Photo, id=photo_id, user=request.user)

    if request.method == "POST":
        form = PhotoEditForm(request.POST, instance=photo)
        if form.is_valid():
            form.save()
            messages.success(request, "Photo updated successfully!")
            return redirect("photos:detail", photo_id=photo.id)
    else:
        form = PhotoEditForm(instance=photo)

    context = {
        "form": form,
        "photo": photo,
    }
    return render(request, "photos/edit.html", context)


@login_required
@require_http_methods(["POST"])
def photo_delete(request, photo_id):
    """Delete a photo"""
    photo = get_object_or_404(Photo, id=photo_id, user=request.user)

    try:
        photo_title = photo.title or "Untitled"
        photo.delete()
        messages.success(request, f'Photo "{photo_title}" deleted successfully!')
        return redirect("photos:gallery")
    except Exception as e:
        messages.error(request, f"Error deleting photo: {str(e)}")
        return redirect("photos:detail", photo_id=photo.id)


@login_required
def photo_stats(request):
    """Display photo statistics and analytics"""
    user_photos = Photo.objects.filter(user=request.user)

    # Basic counts
    total_photos = user_photos.count()
    raw_photos = user_photos.filter(is_raw=True).count()
    public_photos = user_photos.filter(is_public=True).count()
    featured_photos = user_photos.filter(is_featured=True).count()

    # Camera statistics
    camera_stats = (
        user_photos.values("camera_make", "camera_model")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    # Lens statistics
    lens_stats = (
        user_photos.values("lens_model")
        .annotate(count=Count("id"))
        .exclude(lens_model="")
        .order_by("-count")[:10]
    )

    # Monthly upload trends
    monthly_stats = (
        user_photos.extra(select={"month": "strftime('%%Y-%%m', created_at)"})
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    # File size statistics
    total_size = sum(photo.file_size for photo in user_photos)
    avg_size = total_size / total_photos if total_photos > 0 else 0

    # Most used settings
    iso_stats = (
        user_photos.values("iso")
        .annotate(count=Count("id"))
        .exclude(iso__isnull=True)
        .order_by("-count")[:5]
    )

    aperture_stats = (
        user_photos.values("aperture")
        .annotate(count=Count("id"))
        .exclude(aperture__isnull=True)
        .order_by("-count")[:5]
    )

    context = {
        "total_photos": total_photos,
        "raw_photos": raw_photos,
        "public_photos": public_photos,
        "featured_photos": featured_photos,
        "camera_stats": camera_stats,
        "lens_stats": lens_stats,
        "monthly_stats": monthly_stats,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "avg_size_mb": round(avg_size / (1024 * 1024), 2),
        "iso_stats": iso_stats,
        "aperture_stats": aperture_stats,
    }
    return render(request, "photos/stats.html", context)


@login_required
def public_gallery(request):
    """Display public photos from all users"""
    photos = Photo.objects.filter(is_public=True).select_related("user")

    # Apply search if provided
    query = request.GET.get("q", "")
    if query:
        photos = photos.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(tags__icontains=query)
            | Q(user__username__icontains=query)
        )

    # Pagination
    paginator = Paginator(photos, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "query": query,
    }
    return render(request, "photos/public_gallery.html", context)


@login_required
@csrf_exempt
def ajax_upload_progress(request):
    """Handle AJAX upload progress updates"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # This could be used to track upload progress
            # For now, just return success
            return JsonResponse({"status": "success"})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"})

    return JsonResponse({"status": "error", "message": "Invalid request method"})


@login_required
def get_upload_progress(request):
    """Get current upload progress from session"""
    progress = request.session.get("upload_progress", {})
    return JsonResponse(progress)


@login_required
def clear_upload_progress(request):
    """Clear upload progress from session"""
    if "upload_progress" in request.session:
        del request.session["upload_progress"]
    if "upload_errors" in request.session:
        del request.session["upload_errors"]
    request.session.save()
    return JsonResponse({"status": "cleared"})


@login_required
def download_photo(request, photo_id):
    """Download original photo file"""
    photo = get_object_or_404(Photo, id=photo_id, user=request.user)

    if not os.path.exists(photo.original_file.path):
        messages.error(request, "Photo file not found.")
        return redirect("photos:detail", photo_id=photo.id)

    # Create response with file
    response = HttpResponse(
        photo.original_file.read(), content_type="application/octet-stream"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{photo.original_file.name.split("/")[-1]}"'
    )
    return response


@login_required
def bulk_actions(request):
    """Handle bulk actions on multiple photos"""
    if request.method == "POST":
        action = request.POST.get("action")
        photo_ids = request.POST.getlist("photo_ids")

        if not photo_ids:
            messages.error(request, "No photos selected.")
            return redirect("photos:gallery")

        photos = Photo.objects.filter(id__in=photo_ids, user=request.user)

        if action == "delete":
            count = photos.count()
            photos.delete()
            messages.success(request, f"{count} photo(s) deleted successfully!")
        elif action == "make_public":
            photos.update(is_public=True)
            messages.success(request, f"{photos.count()} photo(s) made public!")
        elif action == "make_private":
            photos.update(is_public=False)
            messages.success(request, f"{photos.count()} photo(s) made private!")
        elif action == "add_tags":
            tags_to_add = request.POST.get("tags_to_add", "").strip()
            if tags_to_add:
                for photo in photos:
                    current_tags = photo.get_tags_list()
                    new_tags = [
                        tag.strip() for tag in tags_to_add.split(",") if tag.strip()
                    ]
                    combined_tags = list(set(current_tags + new_tags))
                    photo.tags = ", ".join(combined_tags)
                    photo.save()
                messages.success(request, f"Tags added to {photos.count()} photo(s)!")

        return redirect("photos:gallery")

    return redirect("photos:gallery")
