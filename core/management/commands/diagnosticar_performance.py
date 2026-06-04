import time
from django.core.management.base import BaseCommand
from django.db import connection

from core.services import buscar_catalogo, carregar_catalogo_produtos, catalogo_index_pronto


class Command(BaseCommand):
    help = 'Mede rapidamente pontos de performance do ValiControl no servidor.'

    def handle(self, *args, **options):
        self.stdout.write('=== Diagnóstico de performance ValiControl ===')
        t0 = time.perf_counter()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        self.stdout.write(f'Banco principal respondeu em {(time.perf_counter() - t0) * 1000:.1f} ms')

        t0 = time.perf_counter()
        pronto = catalogo_index_pronto()
        self.stdout.write(f'Catálogo pronto: {pronto} ({(time.perf_counter() - t0) * 1000:.1f} ms)')

        t0 = time.perf_counter()
        total = len(carregar_catalogo_produtos())
        self.stdout.write(f'Total no catálogo: {total} ({(time.perf_counter() - t0) * 1000:.1f} ms)')

        codigo = '7898082113571'
        t0 = time.perf_counter()
        item = buscar_catalogo(codigo)
        self.stdout.write(f'Lookup 1 ({codigo}): {(time.perf_counter() - t0) * 1000:.1f} ms -> {item}')

        t0 = time.perf_counter()
        item = buscar_catalogo(codigo)
        self.stdout.write(f'Lookup cache ({codigo}): {(time.perf_counter() - t0) * 1000:.1f} ms -> {item}')
