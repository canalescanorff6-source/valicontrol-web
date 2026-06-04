from django.conf import settings
import re


def _is_admin_email(email: str) -> bool:
    email = (email or '').strip().lower()
    admin_raw = (
        getattr(settings, 'ADMIN_EMAILS', '')
        or getattr(settings, 'CRIADOR_ADMIN_EMAILS', '')
        or getattr(settings, 'CADASTRO_EMAIL_TRAVADO', '')
        or getattr(settings, 'CADASTRO_AUTORIZACAO_EMAIL', '')
    )
    admins = {item.strip().lower() for item in re.split(r'[,;\s]+', str(admin_raw)) if item.strip()}
    return bool(email and email in admins)


def app_info(request):
    email = ''
    try:
        email = request.session.get('email', '')
    except Exception:
        email = ''
    return {
        'APP_NAME': settings.APP_NAME,
        'usuario_admin': _is_admin_email(email),
    }
