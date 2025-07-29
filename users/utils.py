from django.core.mail import send_mail

def send_2fa_email_code(user, code):
    send_mail(
        "Code de vérification - Connexion",
        f"Bonjour,\n\nVotre code de vérification est : {code}",
        "no-reply@tonsite.com",
        [user.email]
    )

def get_client_ip(request):
    """Récupère l'adresse IP du client depuis l'objet request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip