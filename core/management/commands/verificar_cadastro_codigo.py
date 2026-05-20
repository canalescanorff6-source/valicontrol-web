from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import Client


class Command(BaseCommand):
    help = 'Verifica se a tela /registrar/ renderizada está usando o cadastro autorizado por código.'

    def handle(self, *args, **options):
        self.stdout.write('== Verificação do cadastro autorizado ==')
        self.stdout.write(f'CADASTRO_EMAIL_TRAVADO: {getattr(settings, "CADASTRO_EMAIL_TRAVADO", "") or "não configurado"}')
        self.stdout.write(f'BREVO_SENDER_EMAIL: {getattr(settings, "BREVO_SENDER_EMAIL", "") or "não configurado"}')
        client = Client(HTTP_HOST='testserver')
        response = client.get('/registrar/')
        html = response.content.decode('utf-8', errors='ignore')
        self.stdout.write(f'Status /registrar/: {response.status_code}')
        checks = [
            'CADASTRO PROTEGIDO',
            'Criar conta autorizada',
            'Enviar código para o administrador',
            'Código de autorização',
            'data-screen="cadastro-autorizado-v3"',
        ]
        missing = [item for item in checks if item not in html]
        if missing:
            self.stdout.write(self.style.ERROR('Tela incorreta. Não encontrei: ' + ', '.join(missing)))
            self.stdout.write(html[:1200])
            return
        self.stdout.write(self.style.SUCCESS('Cadastro por código com e-mail travado está ativo na página renderizada.'))
