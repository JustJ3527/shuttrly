# Photo Similarity Test Module

This module contains all testing utilities for the photo similarity system, completely separated from the production code.

## 📁 Structure

```
test/
├── __init__.py
├── apps.py                          # Django app configuration
├── README.md
├── urls.py                          # Test URLs
├── test_views.py                    # Combined test views (advanced + legacy)
├── test_utils.py                    # All similarity and embedding utilities
├── templates/
│   └── test/
│       ├── test_advanced_similarity.html
│       └── test_embedding.html
└── management/
    └── commands/
        ├── test_advanced_similarity.py
        ├── test_hybrid_similarity.py
        ├── test_visual_location.py
        ├── test_faiss_performance.py
        ├── test_navigation.py
        ├── test_interface.py
        ├── debug_test_view.py
        ├── manage_faiss_index.py
        ├── analyze_exif_scores.py
        └── compare_similarity_methods.py
```

## 🚀 Usage

### Web Interface

#### Advanced Similarity Test (Recommended)
```
http://127.0.0.1:8000/photos/test/advanced/
http://127.0.0.1:8000/photos/test/advanced/2/
```

#### Legacy Tests (Backward Compatibility)
```
http://127.0.0.1:8000/photos/test/embedding/
http://127.0.0.1:8000/photos/test/hybrid/
```

### Management Commands

#### FAISS Management
```bash
# Build FAISS index
python manage.py manage_faiss_index build

# Rebuild FAISS index
python manage.py manage_faiss_index rebuild

# Show FAISS statistics
python manage.py manage_faiss_index stats

# Clear FAISS index
python manage.py manage_faiss_index clear
```

#### Performance Testing
```bash
# Test FAISS vs Brute Force performance
python manage.py test_faiss_performance --photo-id 2 --limit 10

# Test Visual + Location similarity
python manage.py test_visual_location

# Test advanced similarity system
python manage.py test_advanced_similarity
```

#### Analysis Commands
```bash
# Analyze EXIF score distribution
python manage.py analyze_exif_scores

# Compare similarity methods
python manage.py compare_similarity_methods

# Debug test view
python manage.py debug_test_view
```

## 🎯 Features

### Advanced Similarity Test
- **6 different methods** comparison
- **FAISS vs Brute Force** performance comparison
- **Real-time statistics** (cache, FAISS index)
- **Interactive navigation** between photos
- **Detailed scoring** (visual, location, EXIF, final)

### FAISS Integration
- **Automatic index management** via Django signals
- **Fallback to brute force** if FAISS fails
- **Performance monitoring** and statistics
- **Persistent index** storage

### Legacy Support
- **Backward compatibility** with old test URLs
- **Gradual migration** path
- **No breaking changes** for existing users

## 🔧 Configuration

### FAISS Settings
Add to your `settings.py`:
```python
# FAISS Index Configuration
FAISS_INDEX_PATH = 'faiss_index.pkl'  # Path to store FAISS index
```

### Template Settings
The test templates are automatically discovered by Django in the `test/templates/` directory.

## 📊 Performance

### Expected Speedups with FAISS
- **Small dataset** (< 100 photos): 2-5x faster
- **Medium dataset** (100-1000 photos): 10-50x faster
- **Large dataset** (> 1000 photos): 50-100x faster

### Memory Usage
- **FAISS Index**: ~2MB per 1000 photos (512D embeddings)
- **Brute Force**: O(n²) memory usage for comparisons

## 🐛 Troubleshooting

### FAISS Not Working
1. Check if FAISS is installed: `pip install faiss-cpu`
2. Rebuild the index: `python manage.py manage_faiss_index rebuild`
3. Check logs for errors

### Template Not Found
1. Ensure `test/templates/` directory exists
2. Check Django template settings
3. Restart Django development server

### Performance Issues
1. Use FAISS instead of brute force
2. Enable caching in similarity calculations
3. Reduce the number of results returned

## 🔄 Migration from Production Code

This module was created by separating test code from production code:

### Moved Files
- `test_views.py` → `test/test_views.py`
- `test_advanced_similarity.html` → `test/templates/test/`
- All `test_*.py` commands → `test/management/commands/`
- Legacy test views → `test/legacy_test_views.py`

### Updated URLs
- Old: `/photos/test-advanced/`
- New: `/photos/test/advanced/`
- Legacy: `/photos/test/embedding/`, `/photos/test/hybrid/`

### Benefits
- **Clean separation** of concerns
- **No pollution** of production code
- **Easier maintenance** and testing
- **Better organization** of test utilities
