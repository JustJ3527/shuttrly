# Batch Upload System with Progress Tracking

## Overview

The photo upload system has been enhanced to handle large numbers of files efficiently through batch processing and real-time progress tracking.

## Key Features

### 1. Batch Processing
- **Batch Size**: Maximum 15 photos processed simultaneously
- **Memory Management**: Prevents server overload by processing in smaller chunks
- **Error Isolation**: If one file fails, others continue processing

### 2. Progress Tracking
- **Real-time Updates**: Progress bar updates every second
- **Batch Information**: Shows current batch being processed
- **File Counters**: Total, processed, uploaded, and failed file counts
- **Status Indicators**: Visual feedback for processing states

### 3. User Experience Improvements
- **Progress Bar**: Animated progress bar with percentage
- **Status Messages**: Clear feedback during upload process
- **Error Handling**: Detailed error reporting for failed files
- **Responsive Design**: Works on all device sizes

## Technical Implementation

### Backend Changes

#### Views (`photos/views.py`)
- Modified `photo_upload()` to process files in batches of 15
- Added session-based progress tracking
- Enhanced error handling and reporting
- Added progress endpoints for AJAX updates

#### New Endpoints
- `GET /photos/upload-progress/` - Retrieve current progress
- `POST /photos/clear-upload-progress/` - Clear progress data

#### Session Data Structure
```python
request.session['upload_progress'] = {
    'total': total_photos,
    'processed': 0,
    'uploaded': 0,
    'failed': 0,
    'current_batch': 0,
    'status': 'processing'  # 'processing', 'completed', 'failed'
}
```

### Frontend Changes

#### Template (`photos/upload.html`)
- Added progress bar section with real-time updates
- Enhanced form with batch size recommendations
- Improved upload tips and guidance

#### JavaScript (`photo_upload_progress.js`)
- Progress tracking class with AJAX updates
- Form submission handling with progress display
- Error handling and user feedback
- Responsive progress updates

#### CSS (`photo_upload.css`)
- Styled progress bar with animations
- Enhanced form styling
- Responsive design improvements

## Usage Guidelines

### Recommended Upload Sizes
- **Optimal**: 15 photos per upload
- **Acceptable**: 15-30 photos (processed in batches)
- **Not Recommended**: 30+ photos (may cause timeouts)

### Performance Considerations
- **RAW Files**: Take longer to process due to EXIF extraction
- **File Size**: Maximum 100MB per file
- **Server Resources**: Batch processing prevents memory issues
- **Network**: Large uploads may take several minutes

## Error Handling

### Common Issues
1. **Thumbnail Generation Failure**: File continues processing without thumbnail
2. **EXIF Extraction Errors**: Photo saved with basic metadata only
3. **File Size Limits**: Files over 100MB are rejected
4. **Format Issues**: Unsupported formats are rejected

### Error Recovery
- Failed files are logged with error details
- Processing continues for remaining files
- User receives detailed error report
- Failed files can be re-uploaded individually

## Monitoring and Debugging

### Server Logs
- Batch processing information
- Individual file processing status
- Error details for failed operations
- Performance metrics

### Session Data
- Progress tracking information
- Error logs for failed uploads
- Upload completion status

## Future Enhancements

### Planned Features
- **Background Processing**: Celery integration for async processing
- **Retry Mechanism**: Automatic retry for failed files
- **Batch Scheduling**: Queue management for large uploads
- **Progress Persistence**: Database storage for long-running uploads

### Performance Optimizations
- **Parallel Processing**: Multiple batches simultaneously
- **Memory Optimization**: Streaming file processing
- **Cache Integration**: Redis for progress tracking
- **CDN Integration**: Faster file delivery

## Troubleshooting

### Progress Bar Not Updating
1. Check browser console for JavaScript errors
2. Verify AJAX endpoints are accessible
3. Check session configuration
4. Clear browser cache and cookies

### Upload Stuck at 0%
1. Verify file selection
2. Check form validation
3. Monitor server logs for errors
4. Ensure proper file permissions

### Batch Processing Issues
1. Check server memory usage
2. Verify file format support
3. Monitor processing timeouts
4. Review error logs

## Configuration

### Django Settings
```python
# Session configuration for progress tracking
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
```

### Batch Size Configuration
```python
# In photos/views.py
BATCH_SIZE = 15  # Adjust based on server capacity
BATCH_DELAY = 0.5  # Delay between batches in seconds
```

## Support

For issues or questions about the batch upload system:
1. Check server logs for error details
2. Review this documentation
3. Test with smaller file batches
4. Contact system administrator

---

*Last updated: August 2025*
*Version: 1.0*
