from django.core.management.base import BaseCommand
from core.services import indexar_catalogo_produtos, catalogo_index_pronto, carregar_catalogo_produtos


class Command(BaseCommand):
    help = 'Cria/atualiza o índice leve SQLite da base data/dados.xlsx.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recria o índice mesmo se ele já estiver atualizado.')
        parser.add_argument('--skip-if-ready', action='store_true', help='Não recria se o índice já estiver pronto.')

    def handle(self, *args, **options):
        if options.get('skip_if_ready') and catalogo_index_pronto():
            total = len(carregar_catalogo_produtos())
            self.stdout.write(self.style.SUCCESS(f'Catálogo já indexado: {total} produto(s).'))
            return

        total = indexar_catalogo_produtos(force=options.get('force', False))
        carregar_catalogo_produtos.cache_clear()
        self.stdout.write(self.style.SUCCESS(f'Catálogo indexado: {total} produto(s).'))
