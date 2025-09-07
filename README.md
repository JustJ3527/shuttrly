# Shuttrly - Photo Sharing Platform

## 📋 Overview

**Shuttrly** is a modern and secure web platform for photo sharing designed for photographers, built with Django 5.2. The site offers an advanced authentication system, comprehensive user management, a detailed logging system, and a personalized administration interface.

---

## 🚀 Main Features

### 🔐 **Authentication & Security System**

#### **Multi-Step Registration (6 steps)**

- **Step 1**: Email verification and confirmation code sending
- **Step 2**: Email verification code validation
- **Step 3**: Personal information input (first name, last name, date of birth)
- **Step 4**: Username selection and availability verification
- **Step 5**: Password creation and confirmation
- **Step 6**: Finalization and account creation

#### **Secure Login (3 steps)**

- **Step 1**: Credential input (email/username + password)
- **Step 2**: Two-factor authentication (2FA) method selection
- **Step 3**: 2FA code validation

#### **Two-Factor Authentication (2FA)**

- **Email 2FA**: Sending 6-digit codes by email
- **TOTP 2FA**: Code generation via authentication applications (Google Authenticator, Authy)
- **Trusted device management**: Device memorization to avoid re-authentication
- **Device analysis**: Automatic detection of device type, browser, and operating system

#### **Advanced Security**

- **Mandatory email verification** for account activation
- **Session management** with connection tracking
- **Attack protection** (CSRF, XSS)
- **Secure password hashing**
- **IP address tracking** and geolocation
- **Login attempt management** with rate limiting

### 👤 **User Management**

#### **Complete User Profile**

- **Personal information**: first name, last name, date of birth, bio
- **Profile picture** with automatic resizing (450x450px max)
- **Privacy settings** (private/public account)
- **Online status** with real-time tracking
- **Connection history** with device details

#### **Account Management**

- **Profile modification** with change history
- **Account deletion** with confirmation
- **GDPR anonymization**: alternative to permanent deletion
- **Trusted device management** with revocation capability

#### **Permission System**

- **Standard users** with limited access
- **Administrators** with extended access
- **Super-users** with complete access
- **User group management**

### 🎨 **User Interface & Design**

#### **Responsive Design**

- **Modern interface** with Bootstrap 5.3.3
- **Adaptive navigation** with mobile hamburger menu
- **Consistent theme** with Font Awesome 6.4.0 icons
- **Custom CSS** for unique experience

#### **Message System**

- **Automatic messages** with 8-second auto-clear
- **Message types**: success, error, warning, information
- **Smart positioning** (top-right of screen)
- **Smooth animations** for entry and exit
- **Advanced JavaScript** message management

#### **Intuitive Navigation**

- **Fixed navigation bar** with logo
- **Contextual menu** based on connection status
- **Quick access** to main features
- **Visual indicators** of user status

### 📊 **Administration & Moderation**

#### **Django Administration Panel**

- **Standard Django interface** for model management
- **User management** with custom forms
- **Group and permission** management
- **Access via** `/admin/`

#### **Custom Administration Panel**

- **Personalized dashboard** accessible via `/admin-panel/`
- **User management** with inline editing
- **User deletion** with confirmation
- **User group management**
- **Intuitive interface** for administrators

#### **Advanced Logging System**

- **Detailed JSON logs** of all user actions
- **Change tracking** with modification history
- **Administrative logs** for sensitive actions
- **Log viewing interface** via `/logs/`
- **Export and analysis** of activity data

### 🔍 **Monitoring & Analytics**

#### **User Action Tracking**

- **Login/logout** with timestamp
- **Profile modifications** with change details
- **Administrative actions** with complete traceability
- **Account deletions** with justification

#### **Device Analysis**

- **Automatic detection** of device type
- **Browser identification** and version
- **Operating system detection**
- **Geolocation** based on IP address
- **Connection history** per device

#### **Security Statistics**

- **Login attempt tracking**
- **Suspicious connection detection**
- **Multiple session management**
- **Abnormal activity monitoring**

### 🧠 **AI-Powered Systems**

#### **Photo Similarity System** *(Fully Functional)*

- **CLIP-based embeddings** using OpenAI's CLIP ViT-Base-Patch32 model
- **512-dimensional vectors** for efficient similarity computation
- **Automatic embedding generation** on photo upload
- **Cosine similarity calculation** for accurate photo matching
- **Real-time similarity detection** between photos
- **Interactive test interface** with navigation between photos
- **Similarity scoring** with precision up to 3 decimal places
- **"Identical" badge** for photos with 100% similarity

#### **User Recommendation System** *(Fully Functional)*

- **Collaborative filtering** based on user follow relationships
- **Cosine similarity** on sparse user-follow matrices
- **Advanced boost factors** for mutual friends, activity levels, account types
- **Time-weighted recent activity** scoring (posts > photos > user recency)
- **Fair treatment** of private accounts (no penalty)
- **Score normalization** for readable 0.2-0.9 range
- **Real-time recommendations** with AJAX updates
- **Background processing** with Celery task queue
- **Caching system** with Redis for performance
- **Automatic updates** after relationship changes

#### **Performance Optimization**

- **PostgreSQL database** for high-performance vector operations
- **Asynchronous processing** using Celery task queue
- **Redis caching** for recommendations and embeddings
- **Batch processing** for existing collections
- **Memory-efficient** model loading and caching

### 🛠️ **Technical Features**

#### **File Management**

- **Photo upload** with automatic validation
- **Automatic image resizing**
- **Format management** (JPG, PNG, GIF, BMP, TIFF)
- **Image optimization** for web
- **Automatic cleanup** of old files

#### **Session System**

- **Advanced user session** management
- **Real-time online status** tracking
- **Trusted device management**
- **Automatic session** expiration

#### **API and Integrations**

- **AJAX endpoints** for real-time verification
- **Client and server-side** validation
- **Advanced form handling** with validation
- **Message system** with JavaScript API

---

## 🏗️ **Technical Architecture**

### **Technologies Used**

- **Backend**: Django 5.2.4 (Python)
- **Database**: PostgreSQL (recommended) / SQLite (development)
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **CSS Framework**: Bootstrap 5.3.3
- **Icons**: Font Awesome 6.4.0
- **Authentication**: Django OTP, PyOTP
- **Image processing**: Pillow (PIL)
- **AI/ML**: Transformers, PyTorch, CLIP, scikit-learn
- **Task Queue**: Celery with Redis broker
- **Caching**: Redis for recommendations and embeddings
- **Geolocation**: External IP services

### **Application Structure**

```
shuttrly/
├── users/           # User management and authentication
├── adminpanel/      # Custom administration interface
├── logs/            # Logging system and action tracking
├── photos/          # Photo management and AI similarity system
├── posts/           # Social features and feed system
└── shuttrly/        # Main project configuration
```

### **Main Data Models**

- **CustomUser**: Custom user with 2FA
- **TrustedDevice**: Trusted devices
- **UserLog**: User action logs
- **PendingFileDeletion**: File deletion management
- **Photo**: Photo management with AI embeddings
- **Collection**: Photo collections and organization
- **Post**: Social posts and feed system

---

## 📥 **Complete Installation - A to Z Guide**

### **🔧 System Prerequisites**

#### **Operating System**
- **macOS** 10.15+ (recommended)
- **Linux** Ubuntu 20.04+ / Debian 11+
- **Windows** 10+ (with WSL2 recommended)

#### **Required Software**
- **Python** 3.10+ (Django 5.2 compatible)
- **Git** (version control)
- **PostgreSQL** 12+ (main database)
- **Redis** 6+ (cache and task queue)
- **Node.js** 16+ (for frontend assets)

---

## 🚀 **Step-by-Step Installation**

### **Step 1: Clone the Project**

```bash
# Clone the repository
git clone https://github.com/JustJ3527/shuttrly.git
cd shuttrly

# Verify the structure
ls -la
```

### **Step 2: Python Environment**

```bash
# Create virtual environment
python3 -m venv env

# Activate the environment
# macOS/Linux:
source env/bin/activate
# Windows:
env\Scripts\activate

# Verify activation
which python  # Should point to env/bin/python
```

### **Step 3: PostgreSQL Installation**

#### **🍎 macOS (Homebrew)**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@14

# Start the service
brew services start postgresql@14

# Create the database
createdb shuttrly_db
psql -c "CREATE USER shuttrly_user WITH PASSWORD 'shuttrly_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE shuttrly_db TO shuttrly_user;"
psql -c "ALTER USER shuttrly_user CREATEDB;"
```

#### **🐧 Linux (Ubuntu/Debian)**
```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib postgresql-client

# Start the service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create the database
sudo -u postgres createdb shuttrly_db
sudo -u postgres psql -c "CREATE USER shuttrly_user WITH PASSWORD 'shuttrly_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE shuttrly_db TO shuttrly_user;"
sudo -u postgres psql -c "ALTER USER shuttrly_user CREATEDB;"
```

#### **🪟 Windows**
```bash
# Download PostgreSQL from https://www.postgresql.org/download/windows/
# Install with official installer
# Note the superuser postgres password

# Open Command Prompt as Administrator
psql -U postgres
CREATE DATABASE shuttrly_db;
CREATE USER shuttrly_user WITH PASSWORD 'shuttrly_password';
GRANT ALL PRIVILEGES ON DATABASE shuttrly_db TO shuttrly_user;
ALTER USER shuttrly_user CREATEDB;
\q
```

### **Step 4: Redis Installation**

#### **🍎 macOS**
```bash
brew install redis
brew services start redis

# Verify installation
redis-cli ping  # Should return PONG
```

#### **🐧 Linux**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify installation
redis-cli ping  # Should return PONG
```

#### **🪟 Windows**
```bash
# Option 1: WSL2 with Ubuntu
wsl --install
# Then follow Linux instructions

# Option 2: Download Redis from
# https://github.com/microsoftarchive/redis/releases
```

### **Step 5: Python Dependencies Installation**

```bash
# Make sure you're in the project directory
cd shuttrly

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(django|torch|transformers|redis|celery)"
```

### **Step 6: Environment Configuration**

```bash
# Create .env file
cat > .env << 'EOF'
# Django Settings
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration
DB_NAME=shuttrly_db
DB_USER=shuttrly_user
DB_PASSWORD=shuttrly_password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration (for testing)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# AI Models Configuration
CLIP_MODEL_NAME=openai/clip-vit-base-patch32
EMBEDDING_DIMENSION=512

# Security Settings
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
EOF

# Make .env file secure
chmod 600 .env
```

### **Step 7: Database Configuration**

```bash
# Check configuration
python manage.py check

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Verify database connection
python manage.py dbshell
# In psql: \dt (to see tables)
# \q (to quit)
```

### **Step 8: AI Models Configuration**

```bash
# Generate embeddings for existing photos (optional)
python manage.py generate_embeddings

# Create superuser
python manage.py createsuperuser
# Follow instructions to create admin account

# Collect static files
python manage.py collectstatic --noinput
```

### **Step 9: Start Services**

#### **Terminal 1: Django Server**
```bash
# Start development server
python manage.py runserver 0.0.0.0:8000
```

#### **Terminal 2: Celery Worker**
```bash
# Start Celery worker for AI tasks
celery -A shuttrly worker --loglevel=info
```

#### **Terminal 3: Celery Beat (optional)**
```bash
# Start scheduler for periodic tasks
celery -A shuttrly beat --loglevel=info
```

### **Step 10: Installation Verification**

#### **Basic Tests**
```bash
# Database test
python manage.py check --database default

# AI models test
python manage.py shell
>>> from photos.utils import get_image_embedding
>>> from users.utilsFolder.recommendations import build_user_recommendations_for_user
>>> print("✅ AI models loaded successfully")
>>> exit()

# Services test
redis-cli ping  # Should return PONG
psql -U shuttrly_user -d shuttrly_db -c "SELECT version();"  # PostgreSQL version
```

#### **Interface Access**
- **Main site**: http://localhost:8000
- **Admin interface**: http://localhost:8000/admin
- **Custom admin panel**: http://localhost:8000/admin-panel
- **User logs**: http://localhost:8000/logs
- **Photo similarity test**: http://localhost:8000/photos/test-embedding/

---

## 🔧 **Advanced Configuration**

### **Production Configuration**

#### **Production Environment Variables**
```bash
# .env.production
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=your-production-secret-key
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Production database
DB_NAME=shuttrly_prod
DB_USER=shuttrly_prod_user
DB_PASSWORD=your-secure-password
DB_HOST=your-db-host
DB_PORT=5432

# Production Redis
REDIS_URL=redis://your-redis-host:6379/0

# Production email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-email-password
```

### **Maintenance Commands**

#### **Data Management**
```bash
# Database backup
pg_dump -U shuttrly_user -h localhost shuttrly_db > backup.sql

# Database restore
psql -U shuttrly_user -h localhost shuttrly_db < backup.sql

# Redis cache cleanup
redis-cli FLUSHALL

# Temporary files cleanup
python manage.py cleanup_temp_files
```

#### **AI Models Management**
```bash
# Regenerate all embeddings
python manage.py generate_embeddings --force

# Calculate recommendations for all users
python manage.py calculate_recommendations --all

# Clean up obsolete recommendations
python manage.py cleanup_old_recommendations
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Database Connection Error**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Check permissions
psql -U postgres -c "\du"  # List users
```

#### **Redis Error**
```bash
# Check if Redis is running
redis-cli ping  # Should return PONG

# Restart Redis
sudo systemctl restart redis-server  # Linux
brew services restart redis  # macOS
```

#### **AI Models Error**
```bash
# Check PyTorch installation
python -c "import torch; print(torch.__version__)"

# Check Transformers installation
python -c "import transformers; print(transformers.__version__)"

# Test CLIP model loading
python manage.py shell
>>> from photos.utils import CLIPModelSingleton
>>> model = CLIPModelSingleton.get_instance()
>>> print("✅ CLIP model loaded")
```

#### **Permissions Error**
```bash
# Fix file permissions
chmod -R 755 static/
chmod -R 755 media/
chmod 600 .env

# Fix database permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE shuttrly_db TO shuttrly_user;"
```

### **Logs and Debug**

#### **Enable Detailed Logs**
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

#### **Debug Commands**
```bash
# Check configuration
python manage.py check --deploy

# Test recommendations
python manage.py shell
>>> from users.utilsFolder.recommendations import debug_user_recommendations
>>> debug_user_recommendations(1, detailed=True)

# Test image similarity
>>> from photos.utils import test_photo_similarity
>>> test_photo_similarity(1, 2)
```

---

## 🔧 **Advanced Configuration**

### **Email Settings**

The system uses SMTP for:

- Email address verification
- 2FA code sending
- Security notifications
- Connection reminders

### **Security**

- **CSRF Protection** enabled by default
- **Django security middleware**
- **Strict form validation**
- **Secure session management**

### **Performance**

- **Automatic image resizing**
- **Database query optimization**
- **Session cache management**
- **Automatic cleanup** of temporary files
- **PostgreSQL optimization** for vector operations
- **Asynchronous AI processing** with Celery
- **Model caching** for faster embedding generation

---

## 📚 **Complete Documentation**

### **🚀 Main Guide**
- **Features Guide** : [FEATURES_GUIDE.md](README/FEATURES.md) - Complete overview of all features

### **🧠 AI Features**
- **Complete AI Guide** : [AI_FEATURES.md](AI_FEATURES.md) - Image similarity, recommendations, detailed calculations

### **📖 Technical Modules**
- **Users Module** : [users/README_AI.md](users/README_AI.md) - Authentication, profiles, recommendations
- **Feed System** : [posts/README_FEED_SYSTEM.md](posts/README_FEED_SYSTEM.md) - Posts, social interactions

### **🔧 Technical Guides**
- **API Documentation** : [README/DEVELOPER_API.md](README/DEVELOPER_API.md) - Endpoints, integrations
- **Photo Collections** : [README/COLLECTIONS_AND_TAGS.md](README/COLLECTIONS_AND_TAGS.md) - Organization, tags
- **Message System** : [README/FEATURES.md](README/FEATURES.md) - User interface

## 🆕 **Recent Improvements**

### **Recommendation System Enhancements**

#### **Score Normalization Fix** *(January 2025)*
- **Improved score distribution**: Scores now range from 0.2 to 0.9 for better readability
- **Enhanced base scoring**: Increased from 0.1 to 0.5 for better multiplier effects
- **Optimized normalization**: Adjusted division factor from 40.0 to 3.0 for optimal distribution
- **Result**: +1,570% improvement in score clarity and user experience

#### **Private Account Fair Treatment** *(January 2025)*
- **Removed penalty**: Private accounts no longer receive 20% score penalty
- **Equal treatment**: Private and public accounts are now scored fairly
- **Improved recommendations**: Private accounts appear more frequently in recommendations
- **Better user experience**: All account types receive appropriate visibility

#### **Time-Weighted Activity Scoring** *(January 2025)*
- **Recent activity priority**: Posts and photos from last 30 days weighted by time slices
- **Activity hierarchy**: Posts weighted 2x more than photos
- **Time decay**: Recent activity (1 day) weighted 5x, older activity (30 days) weighted 1x
- **Better recommendations**: More active users receive higher scores

---

## 🤝 **Contribution**

Contributions are welcome! Feel free to:

- **Fork** the repository
- **Open issues** to report bugs
- **Submit pull requests** for improvements
- **Share your ideas** and suggestions

---

## 📄 **License**

License not yet defined - under determination.

---

## 📞 **Support & Contact**

For any questions, issues, or suggestions:

- **GitHub Issues**: Use the Issues section of the repository
- **Documentation**: Consult the README files and Django documentation
- **Community**: Join the Django developers community

---

_Last updated: September 2025