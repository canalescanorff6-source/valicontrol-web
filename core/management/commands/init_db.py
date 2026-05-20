from django.core.management.base import BaseCommand
from django.db import connection


POSTGRES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE,
        senha TEXT,
        token TEXT,
        criado_em TIMESTAMP,
        trial_expira_em TIMESTAMP,
        ativo INTEGER DEFAULT 0,
        device_id TEXT,
        plano TEXT DEFAULT 'trial',
        ip TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id SERIAL PRIMARY KEY,
        codigo TEXT,
        nome TEXT,
        validade TEXT,
        quantidade INTEGER,
        tipo_qtd TEXT DEFAULT 'Un',
        user_email TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY,
        email TEXT,
        acao TEXT,
        criado_em TIMESTAMP DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pagamentos (
        id SERIAL PRIMARY KEY,
        payment_id TEXT UNIQUE,
        email TEXT,
        status TEXT,
        criado_em TIMESTAMP DEFAULT NOW()
    )
    """,
]

SQLITE_SQL = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        senha TEXT,
        token TEXT,
        criado_em TIMESTAMP,
        trial_expira_em TIMESTAMP,
        ativo INTEGER DEFAULT 0,
        device_id TEXT,
        plano TEXT DEFAULT 'trial',
        ip TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        nome TEXT,
        validade TEXT,
        quantidade INTEGER,
        tipo_qtd TEXT DEFAULT 'Un',
        user_email TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        acao TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_id TEXT UNIQUE,
        email TEXT,
        status TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
]

POSTGRES_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_produtos_user_validade ON produtos (user_email, validade)",
    "CREATE INDEX IF NOT EXISTS idx_produtos_user_codigo ON produtos (user_email, codigo)",
    "CREATE INDEX IF NOT EXISTS idx_produtos_user_nome ON produtos (user_email, nome)",
]

SQLITE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_produtos_user_validade ON produtos (user_email, validade)",
    "CREATE INDEX IF NOT EXISTS idx_produtos_user_codigo ON produtos (user_email, codigo)",
    "CREATE INDEX IF NOT EXISTS idx_produtos_user_nome ON produtos (user_email, nome)",
]

POSTGRES_MIGRATIONS = {
    'users': [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS token TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expira_em TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS ativo INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS device_id TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS plano TEXT DEFAULT 'trial'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS ip TEXT",
    ],
    'produtos': [
        "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS tipo_qtd TEXT DEFAULT 'Un'",
        "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS user_email TEXT",
    ],
    'pagamentos': [
        "ALTER TABLE pagamentos ADD COLUMN IF NOT EXISTS status TEXT",
        "ALTER TABLE pagamentos ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP DEFAULT NOW()",
    ],
}

SQLITE_MIGRATIONS = {
    'users': {
        'token': 'ALTER TABLE users ADD COLUMN token TEXT',
        'criado_em': 'ALTER TABLE users ADD COLUMN criado_em TIMESTAMP',
        'trial_expira_em': 'ALTER TABLE users ADD COLUMN trial_expira_em TIMESTAMP',
        'ativo': 'ALTER TABLE users ADD COLUMN ativo INTEGER DEFAULT 0',
        'device_id': 'ALTER TABLE users ADD COLUMN device_id TEXT',
        'plano': "ALTER TABLE users ADD COLUMN plano TEXT DEFAULT 'trial'",
        'ip': 'ALTER TABLE users ADD COLUMN ip TEXT',
    },
    'produtos': {
        'tipo_qtd': "ALTER TABLE produtos ADD COLUMN tipo_qtd TEXT DEFAULT 'Un'",
        'user_email': 'ALTER TABLE produtos ADD COLUMN user_email TEXT',
    },
    'pagamentos': {
        'status': 'ALTER TABLE pagamentos ADD COLUMN status TEXT',
        'criado_em': 'ALTER TABLE pagamentos ADD COLUMN criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    },
}


class Command(BaseCommand):
    help = 'Cria/atualiza as tabelas usadas pelo ValiControl Web sem apagar dados existentes.'

    def handle(self, *args, **options):
        vendor = connection.vendor
        with connection.cursor() as cursor:
            if vendor == 'postgresql':
                for sql in POSTGRES_SQL:
                    cursor.execute(sql)
                for comandos in POSTGRES_MIGRATIONS.values():
                    for sql in comandos:
                        cursor.execute(sql)
                for sql in POSTGRES_INDEXES:
                    cursor.execute(sql)
            else:
                for sql in SQLITE_SQL:
                    cursor.execute(sql)
                for tabela, colunas in SQLITE_MIGRATIONS.items():
                    cursor.execute(f'PRAGMA table_info({tabela})')
                    existentes = {row[1] for row in cursor.fetchall()}
                    for coluna, sql in colunas.items():
                        if coluna not in existentes:
                            cursor.execute(sql)
                for sql in SQLITE_INDEXES:
                    cursor.execute(sql)

        self.stdout.write(self.style.SUCCESS('Banco ValiControl OK.'))
