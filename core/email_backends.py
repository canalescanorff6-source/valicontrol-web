import logging

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class BrevoEmailBackend(BaseEmailBackend):
    """Backend simples da API Brevo para uso com django.core.mail.send_mail."""

    api_url = 'https://api.brevo.com/v3/smtp/email'

    def send_messages(self, email_messages):
        api_key = (getattr(settings, 'BREVO_API_KEY', '') or '').strip().strip('"').strip("'")
        sender_email = (getattr(settings, 'BREVO_SENDER_EMAIL', '') or '').strip()
        sender_name = (getattr(settings, 'BREVO_SENDER_NAME', '') or 'ValiControl Web').strip()
        timeout = getattr(settings, 'EMAIL_TIMEOUT', 20)

        if not api_key or not sender_email:
            if self.fail_silently:
                return 0
            raise RuntimeError('Configure BREVO_API_KEY e BREVO_SENDER_EMAIL no RunSite.')

        enviados = 0
        for message in email_messages:
            destinatarios = list(message.to or []) + list(message.cc or []) + list(message.bcc or [])
            if not destinatarios:
                continue
            html_content = ''
            for content, mimetype in getattr(message, 'alternatives', []) or []:
                if mimetype == 'text/html':
                    html_content = content
                    break
            payload = {
                'sender': {'name': sender_name, 'email': sender_email},
                'to': [{'email': email} for email in destinatarios],
                'subject': message.subject or '',
                'textContent': message.body or '',
                'htmlContent': html_content or (message.body or '').replace('\n', '<br>'),
            }
            try:
                response = requests.post(
                    self.api_url,
                    headers={'api-key': api_key, 'accept': 'application/json', 'content-type': 'application/json'},
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                enviados += 1
            except Exception:
                logger.exception('Erro ao enviar e-mail pela Brevo')
                if not self.fail_silently:
                    raise
        return enviados
