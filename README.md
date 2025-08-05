# Shuttrly

Shuttrly is a photo-sharing web application for photographers built with Django. Still in development...

---

## 💡 Main Features (for the moment...)

- Custom user registration and authentication
- Photo upload and management
- User profile with profile picture
- JSON-based logging system to track user actions

---

## ⚠️ Prerequisites

- Python 3.10+ (or a version compatible with Django 5.2)
- Pip (Python package manager)
- Git

---

## 📋 Installation

1. **Clone the repository**

```bash
git clone https://github.com/JustJ3527/shuttrly.git
cd shuttrly
```

2. **Create a virtual environment**

```bash
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

.4 **Configure environment variables**

Create a .env file in the root directory (or adjust your configuration method) with the necessary settings (example minimal setup):

```env
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password

# Used for email verification
```

.5 **Apply database migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

.6 **Create a superuser (optional but recommended)**

```bash
python manage.py createsuperuser
```

.7 **Run the development server**

```bash
python manage.py runserver
```
---

## 📸 Viewing the Application

- Open your browser and go to: [http://127.0.0.1:8000](http://127.0.0.1:8000)  
- To access the Django admin panel (if a superuser has been created): [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

---

## ⚠️ Important Notes

- The application uses a **JSON logging system** that stores logs locally in a file.
- Make sure to configure **SMTP settings** correctly to enable email sending (used for registration, confirmation, 2FA, etc.).

---

## 🤝 Contributing

Feel free to **fork** the repository, **open issues**, or **submit pull requests**.  
All contributions are welcome!

---

## 📄 License

Not yet...

---

## 🙏 Thank You

Thank you for using **Shuttrly**!  
