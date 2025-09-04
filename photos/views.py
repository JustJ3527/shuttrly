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

from .models import Photo, Collection, CollectionPhoto
from .forms import PhotoUploadForm, PhotoEditForm, PhotoSearchForm, CollectionCreateForm, CollectionPhotoForm
from .test.test_utils import find_similar_photos_cached
from logs.utils import (
    log_photo_upload_json,
    log_photo_delete_json,
    log_photo_bulk_action_json,
)


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
            is_private = request.POST.get("is_private") == "on"

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
                            is_private=is_private,
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
                            print(
                                f"Processing photo {photo_file.name} (RAW: {photo.is_raw})"
                            )

                            # Extract EXIF data first
                            print(f"Extracting EXIF for {photo_file.name}")
                            photo.extract_exif_data()

                            # Generate thumbnail
                            print(f"Generating thumbnail for {photo_file.name}")
                            photo.generate_thumbnail()

                            # Extract dominant colors for background gradient
                            print(f"Extracting dominant colors for {photo_file.name}")
                            photo.extract_dominant_colors()

                            # Save again with EXIF data, thumbnail, and dominant colors
                            photo.save()

                            # Verify the photo was processed correctly
                            validation_errors = photo.validate_photo_processing()
                            if validation_errors:
                                print(
                                    f"Warning: Photo {photo_file.name} has processing issues: {validation_errors}"
                                )
                                # Still count as uploaded but log the issues
                                uploaded_count += 1
                            else:
                                print(
                                    f"Photo {photo_file.name} processed successfully with all data"
                                )
                                uploaded_count += 1

                            # Log processing status for debugging
                            status = photo.get_processing_status()
                            print(f"Processing status for {photo_file.name}: {status}")

                            # Log photo upload to photo_logs.json
                            try:
                                upload_details = {
                                    "batch_number": batch_num // batch_size + 1,
                                    "photo_number_in_batch": i + 1,
                                    "total_photos": total_photos,
                                    "file_original_name": photo_file.name,
                                    "processing_errors": (
                                        validation_errors if validation_errors else None
                                    ),
                                }

                                log_photo_upload_json(
                                    user=request.user,
                                    photo=photo,
                                    request=request,
                                    upload_details=upload_details,
                                    processing_status=status,
                                    extra_info={
                                        "upload_method": "batch_upload",
                                        "validation_errors": (
                                            validation_errors
                                            if validation_errors
                                            else None
                                        ),
                                    },
                                )
                                
                                # Generate embedding
                                from .tasks import generate_embedding
                                generate_embedding.delay(photo.id)
                                print(f"Embedding task queued for {photo_file.name}")
                                print(f"Photo upload logged for {photo_file.name}")
                            except Exception as log_error:
                                print(
                                    f"Warning: Failed to log photo upload for {photo_file.name}: {log_error}"
                                )

                        except Exception as e:
                            print(f"Error processing photo {photo_file.name}: {e}")
                            import traceback

                            traceback.print_exc()
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
    else:
        # Default sort when no search form is provided
        sort_by = "-date_taken"

    # Always apply sorting with fallback
    if sort_by == "-date_taken":
        # Sort by date_taken with fallback to created_at for photos without EXIF date
        # Add id as final sort to ensure consistent ordering
        photos = photos.order_by("-date_taken", "-created_at", "-id")
    elif sort_by == "date_taken":
        photos = photos.order_by("date_taken", "created_at", "id")
    else:
        photos = photos.order_by(sort_by, "-id")

    # Debug: Print sorting info
    print(f"DEBUG: Photos sorted by: {sort_by}")

    # Calculate statistics BEFORE applying slice
    total_photos = photos.count()
    raw_photos = photos.filter(is_raw=True).count()
    public_photos = photos.filter(is_private=False).count()

    # For lazy loading, get all photos without pagination
    # But limit to a reasonable number to prevent memory issues
    # Apply slice after ordering to maintain sort order
    photos = photos[:1000]
    photos_list = list(photos)  # Convert to list to avoid QuerySet issues

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
        "photos": photos_list,  # List instead of QuerySet
        "search_form": search_form,
        "total_photos": total_photos,
        "raw_photos": raw_photos,
        "public_photos": public_photos,
        "cameras": cameras,
        "lenses": lenses,
    }
    return render(request, "photos/gallery.html", context)


def photo_detail(request, photo_id):
    """Display detailed view of a single photo with EXIF data"""
    photo = get_object_or_404(Photo, id=photo_id)
    
    # Check if user can access this photo
    if not request.user.is_authenticated:
        # Anonymous users can only see public photos
        if photo.is_private:
            messages.error(request, "This photo is private. Please log in to view it.")
            return redirect("photos:gallery")
    elif photo.user != request.user and photo.is_private:
        messages.error(request, "You don't have permission to view this photo.")
        return redirect("photos:gallery")

    # Check user privacy status
    user_is_private = getattr(request.user, 'is_private', False) if request.user.is_authenticated else False

    # Find similar photos using cosine similarity + location with visibility filtering
    # Exclude photos from the connected user to show only photos from other users
    similar_photos = []
    if photo.embedding:
        try:
            from .utils import find_similar_photos_with_visibility
            similar_photos = find_similar_photos_with_visibility(
                photo=photo,
                user=request.user if request.user.is_authenticated else None,
                limit=6,
                threshold=0.6,
                include_own_photos=False  # Exclude own photos for similar photos section
            )
        except Exception as e:
            print(f"Error finding similar photos: {e}")
            similar_photos = []

    context = {
        "photo": photo,
        "similar_photos": similar_photos,
        "user_is_private": user_is_private,
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

        # Log photo deletion before deleting
        try:
            log_photo_delete_json(
                user=request.user,
                photo=photo,
                request=request,
                extra_info={
                    "photo_title": photo_title,
                    "delete_method": "single_delete",
                },
            )
            print(f"Photo deletion logged for {photo_title}")
        except Exception as log_error:
            print(
                f"Warning: Failed to log photo deletion for {photo_title}: {log_error}"
            )

        photo.delete()

        # Check if this is an AJAX request
        if (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.content_type == "application/json"
        ):
            return JsonResponse(
                {
                    "success": True,
                    "message": f'Photo "{photo_title}" deleted successfully!',
                }
            )
        else:
            messages.success(request, f'Photo "{photo_title}" deleted successfully!')
            return redirect("photos:gallery")

    except Exception as e:
        error_message = f"Error deleting photo: {str(e)}"

        # Check if this is an AJAX request
        if (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.content_type == "application/json"
        ):
            return JsonResponse(
                {"success": False, "message": error_message}, status=500
            )
        else:
            messages.error(request, error_message)
            return redirect("photos:detail", photo_id=photo.id)


@login_required
def photo_stats(request):
    """Display photo statistics and analytics"""
    user_photos = Photo.objects.filter(user=request.user)

    # Basic counts
    total_photos = user_photos.count()
    raw_photos = user_photos.filter(is_raw=True).count()
    public_photos = user_photos.filter(is_private=False).count()
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


def public_gallery(request):
    """Display public photos from all users"""
    photos = Photo.objects.filter(is_private=False).select_related("user")

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
            photo_list = list(photos)  # Convert to list before deleting

            # Log bulk deletion
            try:
                log_photo_bulk_action_json(
                    user=request.user,
                    action="delete",
                    photo_ids=[photo.id for photo in photo_list],
                    request=request,
                    results={"deleted_count": count},
                    extra_info={
                        "bulk_action_type": "delete",
                        "photo_titles": [
                            photo.title or "Untitled" for photo in photo_list
                        ],
                    },
                )
                print(f"Bulk photo deletion logged for {count} photos")
            except Exception as log_error:
                print(f"Warning: Failed to log bulk photo deletion: {log_error}")

            photos.delete()
            messages.success(request, f"{count} photo(s) deleted successfully!")

        elif action == "make_public":
            count = photos.count()
            photo_list = list(photos)

            # Log bulk make public
            try:
                log_photo_bulk_action_json(
                    user=request.user,
                    action="make_public",
                    photo_ids=[photo.id for photo in photo_list],
                    request=request,
                    results={"updated_count": count},
                    extra_info={
                        "bulk_action_type": "make_public",
                        "photo_titles": [
                            photo.title or "Untitled" for photo in photo_list
                        ],
                    },
                )
                print(f"Bulk photo make public logged for {count} photos")
            except Exception as log_error:
                print(f"Warning: Failed to log bulk photo make public: {log_error}")

            photos.update(is_private=False)
            messages.success(request, f"{count} photo(s) made public!")

        elif action == "make_private":
            count = photos.count()
            photo_list = list(photos)

            # Log bulk make private
            try:
                log_photo_bulk_action_json(
                    user=request.user,
                    action="make_private",
                    photo_ids=[photo.id for photo in photo_list],
                    request=request,
                    results={"updated_count": count},
                    extra_info={
                        "bulk_action_type": "make_private",
                        "photo_titles": [
                            photo.title or "Untitled" for photo in photo_list
                        ],
                    },
                )
                print(f"Bulk photo make private logged for {count} photos")
            except Exception as log_error:
                print(f"Warning: Failed to log bulk photo make private: {log_error}")

            photos.update(is_private=True)
            messages.success(request, f"{count} photo(s) made private!")

        elif action == "add_tags":
            tags_to_add = request.POST.get("tags_to_add", "").strip()
            if tags_to_add:
                photo_list = list(photos)

                # Log bulk add tags
                try:
                    log_photo_bulk_action_json(
                        user=request.user,
                        action="add_tags",
                        photo_ids=[photo.id for photo in photo_list],
                        request=request,
                        results={
                            "updated_count": len(photo_list),
                            "tags_added": tags_to_add,
                        },
                        extra_info={
                            "bulk_action_type": "add_tags",
                            "photo_titles": [
                                photo.title or "Untitled" for photo in photo_list
                            ],
                            "tags_added": tags_to_add,
                        },
                    )
                    print(f"Bulk photo add tags logged for {len(photo_list)} photos")
                except Exception as log_error:
                    print(f"Warning: Failed to log bulk photo add tags: {log_error}")

                for photo in photo_list:
                    current_tags = photo.get_tags_list()
                    new_tags = [
                        tag.strip() for tag in tags_to_add.split(",") if tag.strip()
                    ]
                    combined_tags = list(set(current_tags + new_tags))
                    photo.tags = ", ".join(combined_tags)
                    photo.save()
                messages.success(request, f"Tags added to {len(photo_list)} photo(s)!")

        return redirect("photos:gallery")

    return redirect("photos:gallery")


@login_required
def photo_gallery_test(request):
    """Simple test gallery to verify photo sorting"""
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
    else:
        # Default sort when no search form is provided
        sort_by = request.GET.get("sort_by", "-date_taken")

    # Always apply sorting with fallback
    if sort_by == "-date_taken":
        # Sort by date_taken with fallback to created_at for photos without EXIF date
        # Add id as final sort to ensure consistent ordering
        photos = photos.order_by("-date_taken", "-created_at", "-id")
    elif sort_by == "date_taken":
        photos = photos.order_by("date_taken", "created_at", "id")
    elif sort_by == "-created_at":
        photos = photos.order_by("-created_at", "-id")
    elif sort_by == "created_at":
        photos = photos.order_by("created_at", "id")
    elif sort_by == "-id":
        photos = photos.order_by("-id")
    elif sort_by == "id":
        photos = photos.order_by("id")
    else:
        photos = photos.order_by(sort_by, "-id")

    # Debug: Print sorting info
    print(f"TEST GALLERY: Photos sorted by: {sort_by}")

    # Calculate statistics BEFORE applying slice
    total_photos = photos.count()
    photos_with_exif = photos.exclude(date_taken__isnull=True).count()
    raw_photos = photos.filter(is_raw=True).count()
    public_photos = photos.filter(is_private=False).count()

    # For test gallery, get all photos without pagination
    # Apply slice after ordering to maintain sort order
    photos = photos[:1000]
    photos_list = list(photos)  # Convert to list to avoid QuerySet issues

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
    print(f"TEST GALLERY: Cameras list: {cameras}")
    print(f"TEST GALLERY: Cameras count: {len(cameras)}")

    context = {
        "photos": photos_list,  # List instead of QuerySet
        "search_form": search_form,
        "total_photos": total_photos,
        "photos_with_exif": photos_with_exif,
        "raw_photos": raw_photos,
        "public_photos": public_photos,
        "cameras": cameras,
        "lenses": lenses,
        "sort_by": sort_by,
    }
    return render(request, "photos/gallery_test.html", context)


# ===============================
# COLLECTIONS
# ===============================

@login_required
def collection_list(request):
    """Display user's collections"""
    collections = Collection.objects.filter(
        Q(owner=request.user) | Q(collaborators=request.user)
    ).distinct().order_by('-updated_at')
    
    context = {
        'collections': collections,
    }
    return render(request, 'photos/collection_list.html', context)


def collection_detail(request, collection_id):
    """Display a specific collection with its photos"""
    collection = get_object_or_404(Collection, id=collection_id)
    
    # Check if user has access to this collection
    if not request.user.is_authenticated:
        # Anonymous users can only see public collections
        if collection.is_private:
            messages.error(request, "This collection is private. Please log in to view it.")
            return redirect('photos:collection_list')
    elif collection.is_private and collection.owner != request.user and request.user not in collection.collaborators.all():
        messages.error(request, "You don't have permission to view this collection.")
        return redirect('photos:collection_list')
    
    # Get photos in the collection with proper ordering
    photos = collection.photos.all().order_by('collection_photos__order', 'collection_photos__added_at')
    
    # Check if user profile is private
    if not request.user.is_authenticated:
        user_is_private = False
    else:
        user_is_private = getattr(request.user, 'is_private', False)
    
    context = {
        'collection': collection,
        'photos': photos,
        'user_is_private': user_is_private,
    }
    return render(request, 'photos/collection_detail.html', context)


@login_required
def collection_create(request):
    """Create a new collection"""
    if request.method == 'POST':
        form = CollectionCreateForm(request.POST)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.owner = request.user
            collection.save()
            
            # Handle collaborators if any
            collaborators = request.POST.getlist('collaborators')
            if collaborators:
                collection.collaborators.set(collaborators)
            
            messages.success(request, f'Collection "{collection.name}" created successfully!')
            return redirect('photos:collection_detail', collection_id=collection.id)
    else:
        form = CollectionCreateForm()
    
    # Get list of users for collaborators
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.exclude(id=request.user.id).order_by('username')
    
    context = {
        'form': form,
        'users': users,
    }
    return render(request, 'photos/collection_form.html', context)


@login_required
def collection_edit(request, collection_id):
    """Edit an existing collection"""
    collection = get_object_or_404(Collection, id=collection_id, owner=request.user)
    
    if request.method == 'POST':
        form = CollectionCreateForm(request.POST, instance=collection)
        if form.is_valid():
            collection = form.save()
            
            # Handle collaborators
            collaborators = request.POST.getlist('collaborators')
            collection.collaborators.set(collaborators)
            
            messages.success(request, f'Collection "{collection.name}" updated successfully!')
            return redirect('photos:collection_detail', collection_id=collection.id)
    else:
        form = CollectionCreateForm(instance=collection)
    
    # Get list of users for collaborators
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.exclude(id=request.user.id).order_by('username')
    
    context = {
        'form': form,
        'collection': collection,
        'users': users,
    }
    return render(request, 'photos/collection_form.html', context)


@login_required
def collection_delete(request, collection_id):
    """Delete a collection"""
    collection = get_object_or_404(Collection, id=collection_id, owner=request.user)
    
    if request.method == 'POST':
        name = collection.name
        collection.delete()
        messages.success(request, f'Collection "{name}" deleted successfully!')
        return redirect('photos:collection_list')
    
    context = {
        'collection': collection,
    }
    return render(request, 'photos/collection_confirm_delete.html', context)


@login_required
def collection_add_photos(request, collection_id):
    """Add photos to a collection"""
    collection = get_object_or_404(Collection, id=collection_id, owner=request.user)
    
    if request.method == 'POST':
        photo_ids_str = request.POST.get('photo_ids', '')
        if photo_ids_str:
            # Split the comma-separated string into a list of integers
            photo_ids = [int(pid.strip()) for pid in photo_ids_str.split(',') if pid.strip().isdigit()]
            if photo_ids:
                photos = Photo.objects.filter(id__in=photo_ids, user=request.user)
            
            for photo in photos:
                # Check if photo is already in collection
                if not collection.photos.filter(id=photo.id).exists():
                    collection.add_photo(photo)
            
            messages.success(request, f'{len(photos)} photo(s) added to collection "{collection.name}"!')
        else:
            messages.warning(request, 'No photos selected.')
        
        return redirect('photos:collection_detail', collection_id=collection.id)
    
    # Get user's photos not in this collection
    available_photos = Photo.objects.filter(user=request.user).exclude(
        collections=collection
    ).order_by('-created_at')
    
    context = {
        'collection': collection,
        'available_photos': available_photos,
    }
    return render(request, 'photos/collection_add_photos.html', context)


@login_required
def collection_remove_photo(request, collection_id, photo_id):
    """Remove a photo from a collection"""
    collection = get_object_or_404(Collection, id=collection_id, owner=request.user)
    photo = get_object_or_404(Photo, id=photo_id)
    
    if request.method == 'POST':
        collection.remove_photo(photo)
        messages.success(request, f'Photo removed from collection "{collection.name}"!')
        return redirect('photos:collection_detail', collection_id=collection.id)
    
    context = {
        'collection': collection,
        'photo': photo,
    }
    return render(request, 'photos/collection_remove_photo.html', context)


@login_required
def collection_reorder_photos(request, collection_id):
    """Reorder photos in a collection via AJAX"""
    if request.method == 'POST' and request.is_ajax():
        collection = get_object_or_404(Collection, id=collection_id, owner=request.user)
        
        try:
            photo_order = json.loads(request.POST.get('photo_order', '[]'))
            collection.reorder_photos(photo_order)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# ===============================
# TAGS
# ===============================

def tag_list(request):
    """Display all tags used by the user"""
    if not request.user.is_authenticated:
        # Anonymous users see all public tags
        user_photos = Photo.objects.filter(is_private=False).exclude(user__is_private=True)
        user_collections = Collection.objects.filter(is_private=False).exclude(owner__is_private=True)
    else:
        # Authenticated users see their own content or all public content based on privacy
        user_is_private = getattr(request.user, 'is_private', False)
        if user_is_private:
            user_photos = Photo.objects.filter(user=request.user)
            user_collections = Collection.objects.filter(owner=request.user)
        else:
            user_photos = Photo.objects.filter(is_private=False).exclude(user__is_private=True)
            user_collections = Collection.objects.filter(is_private=False).exclude(owner__is_private=True)
    
    # Collect all tags from photos
    photo_tags = set()
    for photo in user_photos:
        if photo.tags:
            photo_tags.update(photo.get_tags_list())
    
    # Collect all tags from collections
    collection_tags = set()
    for collection in user_collections:
        if collection.tags:
            collection_tags.update(collection.get_tags_list())
    
    # Combine and sort tags
    all_tags = sorted(list(photo_tags | collection_tags))
    
    # Count usage for each tag
    tag_counts = {}
    for tag in all_tags:
        photo_count = user_photos.filter(tags__icontains=f"#{tag}").count()
        collection_count = user_collections.filter(tags__icontains=f"#{tag}").count()
        tag_counts[tag] = {
            'photo_count': photo_count,
            'collection_count': collection_count,
            'total_count': photo_count + collection_count
        }
    
    context = {
        'tags': all_tags,
        'tag_counts': tag_counts,
    }
    return render(request, 'photos/tag_list.html', context)



def tag_detail(request, tag_name):
    """Display photos and collections with a specific tag"""
    # Remove # if present
    if tag_name.startswith('#'):
        tag_name = tag_name[1:]
    
    # Check if user profile is private
    if not request.user.is_authenticated:
        # Anonymous users see only public content
        user_is_private = False
        photos = Photo.objects.filter(
            tags__icontains=f"#{tag_name}",
            is_private=False
        ).exclude(
            user__is_private=True
        ).order_by('-created_at')
        
        collections = Collection.objects.filter(
            tags__icontains=f"#{tag_name}",
            is_private=False
        ).exclude(
            owner__is_private=True
        ).order_by('-updated_at')
    else:
        user_is_private = getattr(request.user, 'is_private', False)
        
        # Get photos with this tag based on privacy settings
        if user_is_private:
            # If user is private, only show their own photos
            photos = Photo.objects.filter(
                user=request.user,
                tags__icontains=f"#{tag_name}"
            ).order_by('-created_at')
        else:
            # If user is not private, show all non-private photos with this tag
            # but exclude photos from users with private profiles
            photos = Photo.objects.filter(
                tags__icontains=f"#{tag_name}",
                is_private=False
            ).exclude(
                user__is_private=True
            ).order_by('-created_at')
        
        # Get collections with this tag based on privacy settings
        if user_is_private:
            # If user is private, only show their own collections
            collections = Collection.objects.filter(
                owner=request.user,
                tags__icontains=f"#{tag_name}"
            ).order_by('-updated_at')
        else:
            # If user is not private, show all non-private collections with this tag
            # but exclude collections from users with private profiles
            collections = Collection.objects.filter(
                tags__icontains=f"#{tag_name}",
                is_private=False
            ).exclude(
                owner__is_private=True
            ).order_by('-updated_at')
    
    context = {
        'tag_name': tag_name,
        'photos': photos,
        'collections': collections,
        'user_is_private': user_is_private,
    }
    return render(request, 'photos/tag_detail.html', context)


def search_by_tags(request):
    """Search photos and collections by multiple tags"""
    if request.method == 'GET':
        tags = request.GET.get('tags', '').strip()
        if tags:
            # Parse tags (remove # if present and split by space)
            tag_list = [tag.strip().lstrip('#') for tag in tags.split() if tag.strip()]
            
            # Check if user profile is private
            if not request.user.is_authenticated:
                # Anonymous users see only public content
                user_is_private = False
                photos = Photo.objects.filter(is_private=False).exclude(user__is_private=True)
                collections = Collection.objects.filter(is_private=False).exclude(owner__is_private=True)
            else:
                user_is_private = getattr(request.user, 'is_private', False)
                
                # Search photos based on privacy settings
                if user_is_private:
                    # If user is private, only search their own photos
                    photos = Photo.objects.filter(user=request.user)
                else:
                    # If user is not private, search all non-private photos
                    photos = Photo.objects.filter(is_private=False).exclude(user__is_private=True)
                
                # Search collections based on privacy settings
                if user_is_private:
                    # If user is private, only search their own collections
                    collections = Collection.objects.filter(owner=request.user)
                else:
                    # If user is not private, search all non-private collections
                    collections = Collection.objects.filter(is_private=False).exclude(owner__is_private=True)
            
            for tag in tag_list:
                photos = photos.filter(tags__icontains=f"#{tag}")
            
            for tag in tag_list:
                collections = collections.filter(tags__icontains=f"#{tag}")
            
            context = {
                'tags': tag_list,
                'photos': photos.order_by('-created_at'),
                'collections': collections.order_by('-updated_at'),
                'search_query': tags,
                'user_is_private': user_is_private,
            }
            return render(request, 'photos/tag_search_results.html', context)
    
    # If no search or empty search, redirect to tag list
    return redirect('photos:tag_list')


# Test views moved to photos.test.legacy_test_views module


@login_required
def advanced_gallery(request):
    """Advanced gallery with search, selection, and layout options"""
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
    else:
        # Default sort when no search form is provided
        sort_by = "-date_taken"

    # Always apply sorting with fallback
    if sort_by == "-date_taken":
        photos = photos.order_by("-date_taken", "-created_at", "-id")
    elif sort_by == "date_taken":
        photos = photos.order_by("date_taken", "created_at", "id")
    else:
        photos = photos.order_by(sort_by, "-id")

    # Calculate statistics
    total_photos = photos.count()
    raw_photos = photos.filter(is_raw=True).count()
    public_photos = photos.filter(is_private=False).count()

    # For lazy loading, get all photos without pagination
    # But limit to a reasonable number to prevent memory issues
    photos = photos[:1000]
    photos_list = list(photos)  # Convert to list to avoid QuerySet issues

    # Get unique cameras and lenses for filter suggestions
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

    # Get user's collections for bulk actions
    collections = Collection.objects.filter(owner=request.user).order_by('name')

    context = {
        "photos": photos_list,
        "search_form": search_form,
        "total_photos": total_photos,
        "raw_photos": raw_photos,
        "public_photos": public_photos,
        "cameras": cameras,
        "lenses": lenses,
        "collections": collections,
        "debug": settings.DEBUG,
    }
    return render(request, "photos/advanced_gallery.html", context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def add_to_collection(request):
    """Add selected photos to a collection via AJAX"""
    try:
        data = json.loads(request.body)
        photo_ids_str = data.get('photo_ids', '')
        collection_id = data.get('collection_id')
        new_collection_name = data.get('new_collection_name', '').strip()
        
        if not photo_ids_str:
            return JsonResponse({'success': False, 'message': 'No photos selected'})
        
        # Parse photo IDs
        photo_ids = [int(pid.strip()) for pid in photo_ids_str.split(',') if pid.strip().isdigit()]
        if not photo_ids:
            return JsonResponse({'success': False, 'message': 'Invalid photo IDs'})
        
        # Get photos
        photos = Photo.objects.filter(id__in=photo_ids, user=request.user)
        if not photos.exists():
            return JsonResponse({'success': False, 'message': 'No valid photos found'})
        
        # Handle collection
        if collection_id:
            # Add to existing collection
            try:
                collection = Collection.objects.get(id=collection_id, owner=request.user)
            except Collection.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Collection not found'})
        elif new_collection_name:
            # Create new collection
            collection = Collection.objects.create(
                name=new_collection_name,
                owner=request.user,
                description=f"Collection created from {len(photos)} photos"
            )
        else:
            return JsonResponse({'success': False, 'message': 'Please select a collection or enter a new collection name'})
        
        # Add photos to collection
        added_count = 0
        for photo in photos:
            if not collection.photos.filter(id=photo.id).exists():
                collection.add_photo(photo)
                added_count += 1
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully added {added_count} photos to collection "{collection.name}"'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def advanced_bulk_actions(request):
    """Handle advanced bulk actions via AJAX"""
    try:
        data = json.loads(request.body)
        photo_ids_str = data.get('photo_ids', '')
        action = data.get('action')
        
        if not photo_ids_str or not action:
            return JsonResponse({'success': False, 'message': 'Missing required data'})
        
        # Parse photo IDs
        photo_ids = [int(pid.strip()) for pid in photo_ids_str.split(',') if pid.strip().isdigit()]
        if not photo_ids:
            return JsonResponse({'success': False, 'message': 'Invalid photo IDs'})
        
        # Get photos
        photos = Photo.objects.filter(id__in=photo_ids, user=request.user)
        if not photos.exists():
            return JsonResponse({'success': False, 'message': 'No valid photos found'})
        
        if action == 'delete':
            # Bulk delete
            count = photos.count()
            photo_list = list(photos)
            
            # Log bulk deletion
            try:
                log_photo_bulk_action_json(
                    user=request.user,
                    action="delete",
                    photo_ids=[photo.id for photo in photo_list],
                    request=request,
                    results={"deleted_count": count},
                    extra_info={
                        "bulk_action_type": "delete",
                        "photo_titles": [photo.title or "Untitled" for photo in photo_list],
                    },
                )
            except Exception as log_error:
                print(f"Warning: Failed to log bulk photo deletion: {log_error}")
            
            photos.delete()
            return JsonResponse({
                'success': True, 
                'message': f'Successfully deleted {count} photos'
            })
        
        elif action == 'bulk_edit':
            # Bulk edit
            is_private = data.get('is_private')
            tags = data.get('tags', '').strip()
            
            updated_count = 0
            photo_list = list(photos)
            
            for photo in photo_list:
                updated = False
                
                # Update privacy
                if is_private in ['true', 'false']:
                    photo.is_private = (is_private == 'true')
                    updated = True
                
                # Add tags
                if tags:
                    current_tags = photo.get_tags_list()
                    new_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    combined_tags = list(set(current_tags + new_tags))
                    photo.tags = ", ".join(combined_tags)
                    updated = True
                
                if updated:
                    photo.save()
                    updated_count += 1
            
            # Log bulk edit
            try:
                log_photo_bulk_action_json(
                    user=request.user,
                    action="bulk_edit",
                    photo_ids=[photo.id for photo in photo_list],
                    request=request,
                    results={"updated_count": updated_count},
                    extra_info={
                        "bulk_action_type": "bulk_edit",
                        "photo_titles": [photo.title or "Untitled" for photo in photo_list],
                        "is_private": is_private,
                        "tags_added": tags,
                    },
                )
            except Exception as log_error:
                print(f"Warning: Failed to log bulk photo edit: {log_error}")
            
            return JsonResponse({
                'success': True, 
                'message': f'Successfully updated {updated_count} photos'
            })
        
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})