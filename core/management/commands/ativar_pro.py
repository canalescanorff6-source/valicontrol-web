from django.core.management.base import BaseCommand
from core.services import ativar_usuario, normalizar_email


class Command(BaseCommand):
    help = 'Ativa manualmente uma conta como PRO por uma quantidade de dias.'

    def add_arguments(self, parser):
        parser.add_argument('email')
        parser.add_argument('--dias', type=int, default=30)

    def handle(self, *args, **options):
        email = normalizar_email(options['email'])
        dias = options['dias']
        if ativar_usuario(email, dias=dias):
            self.stdout.write(self.style.SUCCESS(f'Conta {email} ativada como PRO por {dias} dias.'))
        else:
            self.stdout.write(self.style.ERROR(f'Conta {email} não encontrada.'))
