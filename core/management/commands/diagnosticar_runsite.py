from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from core.services import catalogo_index_pronto, carregar_catalogo_produtos


class Command(BaseCommand):
    help = 'Mostra um diagnóstico rápido do ValiControl no RunSite.'

    def handle(self, *args, **options):
        self.stdout.write('== ValiControl Web diagnóstico ==')
        self.stdout.write(f'DEBUG: {settings.DEBUG}')
        self.stdout.write(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
        self.stdout.write(f'Database: {connection.vendor}')
        self.stdout.write(f'ASAAS_API_KEY configurada: {bool(settings.ASAAS_API_KEY)}')
        self.stdout.write(f'Webhook token configurado: {bool(settings.ASAAS_WEBHOOK_TOKEN)}')
        self.stdout.write(f'Data Excel existe: {settings.DATA_EXCEL_PATH.exists()} -> {settings.DATA_EXCEL_PATH}')
        self.stdout.write(f'Índice do catálogo pronto: {catalogo_index_pronto()}')
        try:
            self.stdout.write(f'Total no catálogo: {len(carregar_catalogo_produtos())}')
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f'Catálogo ainda não carregou: {exc}'))
        self.stdout.write(f'STATIC_ROOT: {settings.STATIC_ROOT} existe={Path(settings.STATIC_ROOT).exists()}')
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
            self.stdout.write(self.style.SUCCESS('Banco respondeu OK.'))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'Erro no banco: {exc}'))
        call_command('init_db')
