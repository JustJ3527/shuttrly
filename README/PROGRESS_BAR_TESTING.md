# Progress Bar Testing Guide

## Current Issues Identified

1. **Progress bar doesn't appear** during upload
2. **Upload stops mid-process** after ~34 files
3. **JavaScript errors** preventing progress display

## Debug Steps

### 1. Test Progress Bar Display

#### Manual Test:

1. Go to `/photos/upload/`
2. Look for the **Debug section** with test buttons
3. Click **"Test Progress Bar"** button
4. The progress bar should appear with test data
5. Click **"Clear Progress"** to hide it

#### Expected Result:

- Progress bar appears with 50% completion
- Counters show test values (Total: 15, Processed: 7, etc.)
- Debug status shows "Progress bar shown"

### 2. Check Browser Console

#### Open Developer Tools:

1. Press `F12` or right-click → "Inspect"
2. Go to **Console** tab
3. Look for these messages:
   - `"PhotoUploadProgress script loaded successfully"`
   - `"Testing progress bar..."` (when clicking test button)
   - Any error messages in red

#### Common Errors to Look For:

- `ReferenceError: PhotoUploadProgress is not defined`
- `TypeError: Cannot read property of null`
- 404 errors for JavaScript files

### 3. Test File Upload

#### Small Test:

1. Select **5-10 small photos** (JPEG, < 5MB each)
2. Click "Upload Photos"
3. Watch for progress bar appearance
4. Check server logs for batch processing

#### Large Test:

1. Select **15-20 photos** (mix of JPEG and RAW)
2. Click "Upload Photos"
3. Monitor progress bar updates
4. Check for timeout errors

## Troubleshooting

### Progress Bar Not Appearing

#### Check JavaScript Loading:

```html
<!-- Verify this is in the template -->
<script src="{% static 'js/photo_upload_progress.js' %}"></script>
```

#### Check File Path:

```bash
# Verify file exists
ls -la static/js/photo_upload_progress.js
```

#### Check Console Errors:

- Look for 404 errors
- Check for JavaScript syntax errors
- Verify DOM elements exist

### Upload Stopping Mid-Process

#### Check Server Logs:

```bash
# Look for these messages:
"Processing batch X: Y photos"
"Photo saved: ID"
"Extracting EXIF for filename"
"Generating thumbnail for filename"
"Batch X completed. Waiting 0.5s..."
```

#### Common Causes:

1. **Memory exhaustion** - Server runs out of RAM
2. **Timeout** - Request takes too long
3. **File corruption** - Individual file causes crash
4. **Database lock** - SQLite concurrency issues

#### Solutions Implemented:

1. **Batch processing** - 15 files at a time
2. **Progress tracking** - Session-based monitoring
3. **Error isolation** - Continue on individual failures
4. **Timeout settings** - Increased limits

## Performance Monitoring

### Server Resources:

- **Memory usage** during upload
- **CPU usage** for image processing
- **Disk I/O** for file operations
- **Database performance** for metadata storage

### Upload Metrics:

- **Files per batch**: 15 (configurable)
- **Batch delay**: 0.5 seconds
- **Progress updates**: Every second
- **Timeout limits**: 10 minutes total

## Expected Behavior

### Successful Upload:

1. **Progress bar appears** immediately after form submission
2. **Batch counter** increments (1, 2, 3...)
3. **File counters** update in real-time
4. **Progress bar** fills to 100%
5. **Redirect** to gallery on completion

### Failed Upload:

1. **Progress bar shows** failed status (red)
2. **Error details** displayed below progress
3. **Partial success** reported (X uploaded, Y failed)
4. **Form remains** accessible for retry

## Testing Checklist

- [ ] Progress bar appears on test button click
- [ ] JavaScript loads without errors
- [ ] Small upload (5-10 files) works
- [ ] Large upload (15-20 files) works
- [ ] Progress updates in real-time
- [ ] Error handling works correctly
- [ ] Session data persists during upload
- [ ] Batch processing logs appear in console

## Next Steps

1. **Test progress bar display** with debug buttons
2. **Verify JavaScript loading** in browser console
3. **Test small upload** to confirm basic functionality
4. **Monitor server logs** for batch processing
5. **Identify specific failure point** in large uploads

---

_Last updated: August 2025_
_Status: Debugging in progress_
