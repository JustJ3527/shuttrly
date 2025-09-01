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

### 🧠 **AI-Powered Photo Similarity System** *(In Development)*

#### **Image Embedding Technology**

- **CLIP-based embeddings** using OpenAI's CLIP ViT-Base-Patch32 model
- **512-dimensional vectors** for efficient similarity computation
- **Automatic embedding generation** on photo upload
- **Cosine similarity calculation** for accurate photo matching

#### **Similarity Search Features**

- **Real-time similarity detection** between photos
- **Interactive test interface** with navigation between photos
- **Similarity scoring** with precision up to 3 decimal places
- **"Identical" badge** for photos with 100% similarity
- **Clickable similarity scores** for detailed analysis

#### **Performance Optimization**

- **PostgreSQL database** for high-performance vector operations
- **Asynchronous embedding generation** using Celery
- **Batch processing** for existing photo collections
- **Memory-efficient** model loading and caching

#### **Development Status**

- ✅ **Core embedding system** - Fully functional
- ✅ **Similarity calculation** - Working with cosine similarity
- ✅ **Test interface** - Interactive photo similarity testing
- 🔄 **Feed integration** - In development
- 🔄 **Collection recommendations** - Planned
- 🔄 **Advanced search** - Planned

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
- **AI/ML**: Transformers, PyTorch, CLIP
- **Task Queue**: Celery (for async embedding generation)
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

## 📥 **Installation & Configuration**

### **Prerequisites**

- Python 3.10+ (Django 5.2 compatible)
- Pip (Python package manager)
- Git
- PostgreSQL 12+ (recommended) or SQLite
- SMTP server (for email sending)
- Redis (for Celery task queue)

### **Installation**

1. **Clone the repository**

```bash
git clone https://github.com/JustJ3527/shuttrly.git
```

2. **Create virtual environment**

```bash
python3 -m venv env
source env/bin/activate  # macOS/Linux
# or
env\Scripts\activate     # Windows
```

3. **Install PostgreSQL** *(Recommended)*

#### **macOS (using Homebrew)**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Create database and user
createdb shuttrly_db
psql -c "CREATE USER shuttrly_user WITH PASSWORD 'shuttrly_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE shuttrly_db TO shuttrly_user;"
```

#### **Windows**
```bash
# Download PostgreSQL installer from https://www.postgresql.org/download/windows/
# Run the installer and follow the setup wizard
# Remember the password you set for the postgres user

# Open Command Prompt as Administrator and run:
psql -U postgres
CREATE DATABASE shuttrly_db;
CREATE USER shuttrly_user WITH PASSWORD 'shuttrly_password';
GRANT ALL PRIVILEGES ON DATABASE shuttrly_db TO shuttrly_user;
\q
```

#### **Linux (Ubuntu/Debian)**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres createdb shuttrly_db
sudo -u postgres psql -c "CREATE USER shuttrly_user WITH PASSWORD 'shuttrly_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE shuttrly_db TO shuttrly_user;"
```

4. **Install Redis** *(For Celery task queue)*

#### **macOS**
```bash
brew install redis
brew services start redis
```

#### **Windows**
```bash
# Download Redis from https://github.com/microsoftarchive/redis/releases
# Or use WSL with Ubuntu installation above
```

#### **Linux**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

5. **Install Python dependencies**

```bash
cd shuttrly
pip install -r requirements.txt
```

6. **Environment variables configuration**
   Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL)
DB_NAME=shuttrly_db
DB_USER=shuttrly_user
DB_PASSWORD=shuttrly_password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration
EMAIL_HOST=smtp.your_provider.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0
```

7. **Apply migrations**

```bash
python manage.py check # Check if there are no errors
python manage.py makemigrations
python manage.py migrate
```

8. **Generate AI embeddings for existing photos** *(Optional)*

```bash
# Generate embeddings for all existing photos
python manage.py generate_embeddings
```

9. **Start Celery worker** *(For AI processing)*

```bash
# In a separate terminal
celery -A shuttrly worker --loglevel=info
```

10. **Create superuser**

```bash
python manage.py createsuperuser
```

11. **Launch development server**

```bash
python manage.py runserver
```

### **Application Access**

- **Main site**: http://127.0.0.1:8000
- **Django Admin**: http://127.0.0.1:8000/admin
- **Custom admin panel**: http://127.0.0.1:8000/admin-panel
- **User logs**: http://127.0.0.1:8000/logs
- **Photo similarity test**: http://127.0.0.1:8000/photos/test-embedding/

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

## 📚 **Additional Documentation**

- **Message System**: [FEATURES.md](README/FEATURES.md)
- **Login Structure**: [FEATURES_DESCRIPTION.md](README/FEATURES_DESCRIPTION.md)
- **Photo Collections**: [COLLECTIONS_AND_TAGS.md](README/COLLECTIONS_AND_TAGS.md)
- **Feed System**: [README_FEED_SYSTEM.md](posts/README_FEED_SYSTEM.md)
- **API Documentation**: [DEVELOPER_API.md](README/DEVELOPER_API.md)

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