from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.test import Client


class Command(BaseCommand):
    help = 'Verifica se a tela de cadastro por código está instalada e ativa.'

    def handle(self, *args, **options):
        template_path = Path(settings.BASE_DIR) / 'templates' / 'core' / 'registrar.html'
        html_file = template_path.read_text(encoding='utf-8') if template_path.exists() else ''
        marcadores = [
            'CADASTRO AUTORIZADO',
            'Enviar código para o administrador',
            'Código de autorização',
            'Criar conta autorizada',
        ]
        self.stdout.write('== Cadastro por código ==')
        self.stdout.write(f'Template: {template_path}')
        self.stdout.write(f'Template existe: {template_path.exists()}')
        for item in marcadores:
            self.stdout.write(f'Marcador "{item}": {item in html_file}')
        self.stdout.write(f'Obrigatório: {getattr(settings, "CADASTRO_AUTORIZACAO_OBRIGATORIA", None)}')
        self.stdout.write(f'E-mail que recebe código: {getattr(settings, "CADASTRO_AUTORIZACAO_EMAIL", "")}')
        self.stdout.write(f'Remetente Brevo: {getattr(settings, "BREVO_SENDER_EMAIL", "")}')

        client = Client(HTTP_HOST='testserver')
        response = client.get(reverse('core:registrar'))
        body = response.content.decode('utf-8', errors='replace')
        self.stdout.write(f'GET /registrar/: {response.status_code}')
        for item in marcadores:
            self.stdout.write(f'HTML renderizado contém "{item}": {item in body}')

        if response.status_code == 200 and all(item in body for item in marcadores):
            self.stdout.write(self.style.SUCCESS('Cadastro por código está ativo na página renderizada.'))
        else:
            self.stdout.write(self.style.ERROR('Cadastro por código NÃO apareceu na página renderizada.'))
