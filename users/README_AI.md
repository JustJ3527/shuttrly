# Users Module Documentation

## 📋 Overview

The Users module is the core authentication and user management system for Shuttrly. It provides comprehensive user registration, authentication, profile management, and social features with advanced security measures and AI-powered recommendations.

---

## 🏗️ Module Architecture

### **Core Components**

```
users/
├── models.py              # User models and relationships
├── views.py               # Authentication and profile views
├── forms.py               # Form definitions and validation
├── utils.py               # Utility functions and helpers
├── tasks.py               # Background tasks (Celery)
├── signals.py             # Django signal handlers
├── middleware.py          # Custom middleware
├── validators.py          # Custom field validators
├── constants.py           # Module constants
├── context_processors.py  # Template context processors
├── backend.py             # Custom authentication backend
├── admin.py               # Django admin configuration
├── apps.py                # App configuration
├── urls.py                # URL routing
├── tests.py               # Test cases
├── utilsFolder/           # Utility modules
│   └── recommendations.py # AI recommendation system
├── api/                   # REST API endpoints
├── management/            # Django management commands
├── migrations/            # Database migrations
├── templates/             # HTML templates
└── templatetags/          # Custom template tags
```

---

## 🔐 Authentication System

### **Multi-Step Registration (6 Steps)**

#### **Step 1: Email Verification**
- User enters email address
- System generates 6-digit verification code
- Code sent via email with 10-minute expiry
- Temporary user created for session management

#### **Step 2: Email Code Verification**
- User enters verification code
- Code validation with 3 attempt limit
- Session timeout management
- Automatic cleanup of temporary users

#### **Step 3: Personal Information**
- First name, last name, date of birth
- Age validation (minimum 16 years)
- Data validation and sanitization

#### **Step 4: Username Selection**
- Real-time username availability checking
- Username validation (3-30 characters, alphanumeric + underscore)
- Case-insensitive uniqueness check
- AJAX validation for instant feedback

#### **Step 5: Password Creation**
- Password strength validation
- Confirmation matching
- Secure password hashing

#### **Step 6: Account Finalization**
- Data validation and account creation
- Automatic user login
- Welcome message and redirect

### **Secure Login System (3 Steps)**

#### **Step 1: Credentials Validation**
- Email/username + password authentication
- Account status verification
- Trusted device detection

#### **Step 2: 2FA Method Selection** (if enabled)
- Choice between email and TOTP 2FA
- Method-specific code generation
- Session data initialization

#### **Step 3: 2FA Verification**
- Code validation (email or TOTP)
- Trusted device registration
- Session establishment

### **Two-Factor Authentication (2FA)**

#### **Email 2FA**
- 6-digit codes sent via email
- 2-minute resend cooldown
- 10-minute code expiry
- Secure code generation

#### **TOTP 2FA**
- Google Authenticator compatible
- QR code generation for setup
- Time-based one-time passwords
- Backup codes support

#### **Trusted Device Management**
- Device fingerprinting
- Automatic device recognition
- Device revocation capability
- Connection history tracking

---

## 👤 User Management

### **User Model (CustomUser)**

#### **Core Fields**
```python
# Identity
email = models.EmailField(unique=True)
username = models.CharField(max_length=30, unique=True)
first_name = models.CharField(max_length=30)
last_name = models.CharField(max_length=40)
date_of_birth = models.DateField()

# Profile
bio = models.TextField(blank=True)
is_private = models.BooleanField(default=False)
profile_picture = models.ImageField()
banner = models.ImageField()

# Security
is_email_verified = models.BooleanField(default=False)
email_2fa_enabled = models.BooleanField(default=False)
totp_enabled = models.BooleanField(default=False)

# Status
is_active = models.BooleanField(default=True)
is_online = models.BooleanField(default=False)
last_login_date = models.DateTimeField()
```

#### **Relationship Methods**
```python
# Social relationships
def get_followers(self)           # Users following this user
def get_following(self)           # Users this user follows
def get_friends(self)             # Mutual followers
def get_close_friends(self)       # Close friend relationships
def is_following(self, user)      # Check follow status
def is_followed_by(self, user)    # Check follower status

# Privacy and visibility
def can_see_profile(self, viewer) # Profile visibility check
def get_relationship_status_with(self, other_user) # Relationship status

# Activity metrics
def get_photos_count(self)        # Total photos uploaded
def get_posts_count(self)         # Total posts created
def get_likes_received_count(self) # Total likes received
def get_cameras_used(self)        # Unique cameras used
```

### **User Relationships**

#### **UserRelationship Model**
```python
class UserRelationship(models.Model):
    from_user = models.ForeignKey(CustomUser, related_name="relationships_from")
    to_user = models.ForeignKey(CustomUser, related_name="relationships_to")
    relationship_type = models.CharField(choices=[
        ("follow", "Follow"),
        ("close_friend", "Close Friend")
    ])
    created_at = models.DateTimeField(auto_now_add=True)
```

#### **FollowRequest Model**
```python
class FollowRequest(models.Model):
    from_user = models.ForeignKey(CustomUser, related_name='follow_requests_sent')
    to_user = models.ForeignKey(CustomUser, related_name='follow_requests_received')
    status = models.CharField(choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ])
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 🧠 AI Recommendation System

### **Collaborative Filtering Algorithm**

#### **Core Algorithm**
1. **Data Collection**: Extract user follow relationships
2. **Matrix Construction**: Build sparse user-follow matrix
3. **Similarity Calculation**: Compute cosine similarity between users
4. **Score Boosting**: Apply boost factors for various criteria
5. **Recommendation Generation**: Generate top recommendations per user

#### **Boost Factors**
- **Recent Activity**: Up to 10x multiplier (time-weighted: posts > photos)
- **Total Activity**: Up to 3x multiplier (posts weighted 2x photos)
- **Mutual Friends**: +30% per mutual friend
- **Common Following**: +10% per common follow
- **Public Accounts**: +10% boost (no penalty for private accounts)
- **Common Followers**: +5% per common follower
- **New Account**: Up to 10% boost (accounts < 30 days old)
- **Score Normalization**: Final scores in 0.2-0.9 range for readability

#### **Key Functions**
```python
# Main recommendation calculation
def build_user_recommendations()

# Single user recommendations
def build_user_recommendations_for_user(user_id)

# Get recommendations for display
def get_recommendations_for_display(user_id, limit=5)

# Cached recommendations
def get_user_recommendations_cached(user_id, limit=5)
```

### **Background Processing**

#### **Celery Tasks**
```python
# Full recommendation calculation
@shared_task(bind=True, max_retries=3)
def calculate_user_recommendations_task(self, user_id=None, force_recalculate=False)

# Cache management
@shared_task
def update_recommendation_cache(user_id, recommendations)

# Cleanup old data
@shared_task
def cleanup_old_recommendations()
```

#### **Management Commands**
```bash
# Setup periodic tasks
python manage.py setup_recommendations

# Manual calculation
python manage.py calculate_recommendations

# Auto recommendations (fallback)
python manage.py auto_recommendations
```

### **Caching Strategy**

#### **Redis Cache Keys**
- `user_recommendations:{user_id}` - User's recommendations
- `recommendation_stats` - System statistics
- `last_recommendation_update` - Timestamp of last update

#### **Cache TTL**
- User recommendations: 1 hour
- Statistics: 30 minutes
- System status: 10 minutes

---

## 🌐 API Endpoints

### **Authentication Endpoints**

#### **Registration**
```
GET  /register/                    # Registration form
POST /register/                    # Process registration
POST /resend-verification-code/    # Resend verification code
```

#### **Login**
```
GET  /login/                       # Login form
POST /login/                       # Process login
POST /resend-2fa-code/            # Resend 2FA code
```

#### **Profile Management**
```
GET  /profile/                     # Profile view
POST /profile/                     # Update profile
GET  /edit-profile/               # Profile editing form
POST /edit-profile/               # Process profile updates
```

### **Social Features**

#### **User Relationships**
```
POST /ajax/toggle-follow/         # Follow/unfollow user
POST /ajax/send-follow-request/   # Send follow request
POST /ajax/handle-follow-request/ # Accept/reject follow request
POST /ajax/toggle-close-friend/   # Toggle close friend
GET  /ajax/get-relationship-status/ # Get relationship status
```

#### **Recommendations**
```
POST /ajax/refresh-recommendations/ # Refresh recommendations
GET  /ajax/get-recommendations/     # Get current recommendations
```

### **REST API (DRF)**

#### **Recommendations API**
```
GET  /api/v1/recommendations/      # Get recommendations
POST /api/v1/recommendations/trigger/ # Trigger calculation
GET  /api/v1/recommendations/stats/ # Get statistics
POST /api/v1/recommendations/refresh-all/ # Refresh all
```

---

## 🎨 User Interface

### **Templates Structure**

```
templates/users/
├── register.html              # Multi-step registration
├── login.html                 # Multi-step login
├── profile.html               # Profile view
├── edit_profile.html          # Profile editing
├── edit_profile_simple.html   # Simple profile editing
├── public_profile.html        # Public user profiles
├── settings_dashboard.html    # Settings dashboard
├── personal_settings.html     # Personal settings
├── 2fa_settings.html          # 2FA management
└── delete_account_confirm.html # Account deletion
```

### **Settings Categories**

#### **General Settings**
- Email and password management
- Date of birth
- Basic information

#### **Security Settings**
- 2FA configuration
- Trusted device management
- Privacy settings

#### **Profile Settings**
- Public profile information
- Profile picture
- Bio and visibility

#### **Media Settings**
- Profile picture management
- Banner image

#### **Preferences**
- Notification settings
- Language preferences
- Timezone settings

---

## 🔧 Configuration

### **Settings Integration**

#### **Required Settings**
```python
# settings.py
INSTALLED_APPS = [
    'users',
    'django_celery_beat',  # For periodic tasks
]

# Celery configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
    }
}

# Context processors
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                'users.context_processors.recommendations_context',
            ],
        },
    },
]
```

### **Email Configuration**

#### **SMTP Settings**
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.your_provider.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@example.com'
EMAIL_HOST_PASSWORD = 'your_email_password'
DEFAULT_FROM_EMAIL = 'Shuttrly <noreply@shuttrly.com>'
```

### **Security Settings**

#### **2FA Configuration**
```python
# settings.py
OTP_TOTP_ISSUER = 'Shuttrly'
OTP_TOTP_THROTTLE_FACTOR = 1
OTP_EMAIL_SENDER = 'Shuttrly <noreply@shuttrly.com>'
```

---

## 📊 Performance & Monitoring

### **Database Optimization**

#### **Query Optimization**
- `select_related()` for foreign key relationships
- `prefetch_related()` for many-to-many relationships
- Database indexes on frequently queried fields
- Bulk operations for recommendation updates

#### **Caching Strategy**
- Redis caching for recommendations
- Session-based caching for user data
- Template fragment caching
- CDN integration for static assets

### **Background Task Monitoring**

#### **Celery Monitoring**
```bash
# Start Flower monitoring
celery -A shuttrly flower

# Check active tasks
celery -A shuttrly inspect active

# Check task statistics
celery -A shuttrly inspect stats
```

#### **Performance Metrics**
- Recommendation calculation time: 2-5 minutes for 1000 users
- API response time: < 200ms
- Cache hit rate: > 90%
- Database query count: Optimized to < 10 queries per request
- Score distribution: 0.2-0.9 range for optimal readability
- Private account treatment: Equal scoring (no penalty)

---

## 🧪 Testing

### **Test Coverage**

#### **Unit Tests**
- Model validation and methods
- Form validation and processing
- Utility function testing
- API endpoint testing

#### **Integration Tests**
- Complete registration flow
- Login with 2FA
- Recommendation system
- Social relationship management

#### **Performance Tests**
- Load testing for recommendation API
- Database query optimization
- Cache performance testing

### **Running Tests**
```bash
# Run all tests
python manage.py test users

# Run specific test
python manage.py test users.tests.TestUserRegistration

# Run with coverage
coverage run --source='.' manage.py test users
coverage report
coverage html
```

---

## 🚨 Error Handling

### **Exception Handling**

#### **Registration Errors**
- Email validation errors
- Username availability conflicts
- Age restriction violations
- Database constraint violations

#### **Authentication Errors**
- Invalid credentials
- 2FA code failures
- Session timeout handling
- Account lockout protection

#### **Recommendation Errors**
- Insufficient data fallback
- Cache miss handling
- Background task failures
- API timeout handling

### **Logging**

#### **Log Levels**
- **DEBUG**: Detailed operation logs
- **INFO**: General operation logs
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors requiring attention

#### **Log Categories**
- User actions (registration, login, profile updates)
- Security events (failed logins, 2FA attempts)
- System events (recommendation updates, cache operations)
- Error tracking (exceptions, failures)

---

## 🔒 Security Features

### **Data Protection**

#### **Password Security**
- Secure password hashing (Django's PBKDF2)
- Password strength validation
- Password change verification

#### **Session Security**
- Secure session cookies
- Session timeout management
- CSRF protection on all forms
- XSS protection in templates

#### **2FA Security**
- Time-based OTP validation
- Rate limiting on 2FA attempts
- Secure code generation
- Trusted device management

### **Privacy Features**

#### **Profile Privacy**
- Private account option
- Follow request system
- Profile visibility controls
- Data anonymization (GDPR)

#### **Data Retention**
- Automatic cleanup of old data
- Secure file deletion
- Log rotation and archival
- User data export/deletion

---

## 📈 Future Enhancements

### **Planned Features**

#### **Advanced Recommendations**
- Machine learning model integration
- Content-based recommendations using CLIP embeddings
- Real-time recommendation updates after relationship changes
- A/B testing framework
- Enhanced score normalization and distribution
- Fair treatment of all account types

#### **Enhanced Security**
- Biometric authentication
- Advanced threat detection
- Security audit logging
- Compliance reporting

#### **Social Features**
- User groups and communities
- Advanced privacy controls
- Social activity feeds
- User interaction analytics

---

## 📞 Support & Troubleshooting

### **Common Issues**

#### **Registration Problems**
- Email delivery issues
- Username conflicts
- Age validation errors
- Session timeout

#### **Login Issues**
- 2FA code problems
- Trusted device recognition
- Session management
- Password reset

#### **Recommendation Issues**
- Cache invalidation
- Background task failures
- Performance problems
- Data consistency

### **Debug Commands**
```bash
# Check user data
python manage.py shell
>>> from users.models import CustomUser
>>> user = CustomUser.objects.get(username='testuser')
>>> print(user.get_followers().count())

# Test recommendations
python manage.py shell
>>> from users.utilsFolder.recommendations import get_recommendations_for_display
>>> recs = get_recommendations_for_display(user.id)
>>> print(recs)

# Check background tasks
celery -A shuttrly inspect active
celery -A shuttrly inspect scheduled
```

---

_Last updated: January 2025_
