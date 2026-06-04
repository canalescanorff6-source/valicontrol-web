from django.conf import settings
from django.core.management.base import BaseCommand
from core.services import solicitar_codigo_autorizacao


class Command(BaseCommand):
    help = 'Verifica variáveis da Brevo e, opcionalmente, envia um código de teste.'

    def add_arguments(self, parser):
        parser.add_argument('--teste', default='', help='Usuário/e-mail de teste para gerar código, ex: teste@validade.app')

    def handle(self, *args, **options):
        self.stdout.write('== Diagnóstico de e-mail ValiControl ==')
        self.stdout.write(f'BREVO_API_KEY configurada: {bool(getattr(settings, "BREVO_API_KEY", ""))}')
        self.stdout.write(f'BREVO_SENDER_EMAIL: {getattr(settings, "BREVO_SENDER_EMAIL", "") or "não configurado"}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {getattr(settings, "DEFAULT_FROM_EMAIL", "") or "não configurado"}')
        self.stdout.write(f'CADASTRO_EMAIL_TRAVADO: {getattr(settings, "CADASTRO_EMAIL_TRAVADO", "") or "não configurado"}')
        self.stdout.write(f'CADASTRO_AUTORIZACAO_EMAIL: {getattr(settings, "CADASTRO_AUTORIZACAO_EMAIL", "") or "não configurado"}')
        teste = (options.get('teste') or '').strip()
        if not teste:
            self.stdout.write('Para enviar teste: python manage.py diagnosticar_email --teste teste@validade.app')
            return
        resultado, erro = solicitar_codigo_autorizacao(teste, 'diagnostico-runsite')
        if erro:
            self.stdout.write(self.style.ERROR(f'Erro ao enviar teste: {erro}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Código de teste solicitado para {resultado.get("email")}. Confira o e-mail administrativo.'))
