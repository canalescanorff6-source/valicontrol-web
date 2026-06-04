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
        quantidade INTEGER DEFAULT 0,
        tipo_qtd TEXT DEFAULT 'Un',
        user_email TEXT,
        lote TEXT,
        categoria TEXT,
        fornecedor TEXT,
        localizacao TEXT,
        observacao TEXT,
        valor_unitario DOUBLE PRECISION DEFAULT 0,
        criado_em TIMESTAMP DEFAULT NOW(),
        atualizado_em TIMESTAMP DEFAULT NOW()
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
    """
    CREATE TABLE IF NOT EXISTS codigos_autorizacao (
        id SERIAL PRIMARY KEY,
        email TEXT NOT NULL,
        codigo_hash TEXT NOT NULL,
        ip TEXT,
        canal TEXT,
        criado_em TIMESTAMP DEFAULT NOW(),
        expira_em TIMESTAMP,
        usado_em TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS baixas_estoque (
        id SERIAL PRIMARY KEY,
        produto_id INTEGER,
        user_email TEXT,
        quantidade INTEGER DEFAULT 0,
        motivo TEXT DEFAULT 'retirada',
        observacao TEXT,
        criado_em TIMESTAMP DEFAULT NOW()
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS configuracoes_sistema (
        chave TEXT PRIMARY KEY,
        valor TEXT,
        atualizado_em TIMESTAMP DEFAULT NOW()
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
        quantidade INTEGER DEFAULT 0,
        tipo_qtd TEXT DEFAULT 'Un',
        user_email TEXT,
        lote TEXT,
        categoria TEXT,
        fornecedor TEXT,
        localizacao TEXT,
        observacao TEXT,
        valor_unitario REAL DEFAULT 0,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    """
    CREATE TABLE IF NOT EXISTS codigos_autorizacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        codigo_hash TEXT NOT NULL,
        ip TEXT,
        canal TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expira_em TIMESTAMP,
        usado_em TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS baixas_estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER,
        user_email TEXT,
        quantidade INTEGER DEFAULT 0,
        motivo TEXT DEFAULT 'retirada',
        observacao TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS configuracoes_sistema (
        chave TEXT PRIMARY KEY,
        valor TEXT,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
]

POSTGRES_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_produtos_user_validade ON produtos (user_email, validade)",
    "CREATE INDEX IF NOT EXISTS idx_produtos_user_codigo ON produtos (user_email, codigo)",
    "CREATE INDEX IF NOT EXISTS idx_produtos_user_nome ON produtos (user_email, nome)",
    "CREATE INDEX IF NOT EXISTS idx_produtos_user_lote ON produtos (user_email, lote)",
    "CREATE INDEX IF NOT EXISTS idx_produtos_user_categoria ON produtos (user_email, categoria)",
    "CREATE INDEX IF NOT EXISTS idx_codigos_autorizacao_email_hash ON codigos_autorizacao (email, codigo_hash)",
    "CREATE INDEX IF NOT EXISTS idx_codigos_autorizacao_expira ON codigos_autorizacao (expira_em)",
    "CREATE INDEX IF NOT EXISTS idx_baixas_user_produto ON baixas_estoque (user_email, produto_id)",
    "CREATE INDEX IF NOT EXISTS idx_baixas_user_criado ON baixas_estoque (user_email, criado_em)",
    "CREATE INDEX IF NOT EXISTS idx_configuracoes_chave ON configuracoes_sistema (chave)",
]

SQLITE_INDEXES = POSTGRES_INDEXES

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
        "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS lote TEXT",
        "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS categoria TEXT",
        "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS fornecedor TEXT",
        "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS localizacao TEXT",
        "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS observacao TEXT",
        "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS valor_unitario DOUBLE PRECISION DEFAULT 0",
        "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP DEFAULT NOW()",
        "ALTER TABLE produtos ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMP DEFAULT NOW()",
    ],
    'pagamentos': [
        "ALTER TABLE pagamentos ADD COLUMN IF NOT EXISTS status TEXT",
        "ALTER TABLE pagamentos ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP DEFAULT NOW()",
    ],
    'codigos_autorizacao': [
        "ALTER TABLE codigos_autorizacao ADD COLUMN IF NOT EXISTS ip TEXT",
        "ALTER TABLE codigos_autorizacao ADD COLUMN IF NOT EXISTS canal TEXT",
        "ALTER TABLE codigos_autorizacao ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP DEFAULT NOW()",
        "ALTER TABLE codigos_autorizacao ADD COLUMN IF NOT EXISTS expira_em TIMESTAMP",
        "ALTER TABLE codigos_autorizacao ADD COLUMN IF NOT EXISTS usado_em TIMESTAMP",
    ],
    'baixas_estoque': [
        "ALTER TABLE baixas_estoque ADD COLUMN IF NOT EXISTS produto_id INTEGER",
        "ALTER TABLE baixas_estoque ADD COLUMN IF NOT EXISTS user_email TEXT",
        "ALTER TABLE baixas_estoque ADD COLUMN IF NOT EXISTS quantidade INTEGER DEFAULT 0",
        "ALTER TABLE baixas_estoque ADD COLUMN IF NOT EXISTS motivo TEXT DEFAULT 'retirada'",
        "ALTER TABLE baixas_estoque ADD COLUMN IF NOT EXISTS observacao TEXT",
        "ALTER TABLE baixas_estoque ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP DEFAULT NOW()",
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
        'lote': 'ALTER TABLE produtos ADD COLUMN lote TEXT',
        'categoria': 'ALTER TABLE produtos ADD COLUMN categoria TEXT',
        'fornecedor': 'ALTER TABLE produtos ADD COLUMN fornecedor TEXT',
        'localizacao': 'ALTER TABLE produtos ADD COLUMN localizacao TEXT',
        'observacao': 'ALTER TABLE produtos ADD COLUMN observacao TEXT',
        'valor_unitario': 'ALTER TABLE produtos ADD COLUMN valor_unitario REAL DEFAULT 0',
        'criado_em': 'ALTER TABLE produtos ADD COLUMN criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'atualizado_em': 'ALTER TABLE produtos ADD COLUMN atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    },
    'pagamentos': {
        'status': 'ALTER TABLE pagamentos ADD COLUMN status TEXT',
        'criado_em': 'ALTER TABLE pagamentos ADD COLUMN criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
    },
    'codigos_autorizacao': {
        'ip': 'ALTER TABLE codigos_autorizacao ADD COLUMN ip TEXT',
        'canal': 'ALTER TABLE codigos_autorizacao ADD COLUMN canal TEXT',
        'criado_em': 'ALTER TABLE codigos_autorizacao ADD COLUMN criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'expira_em': 'ALTER TABLE codigos_autorizacao ADD COLUMN expira_em TIMESTAMP',
        'usado_em': 'ALTER TABLE codigos_autorizacao ADD COLUMN usado_em TIMESTAMP',
    },
    'baixas_estoque': {
        'produto_id': 'ALTER TABLE baixas_estoque ADD COLUMN produto_id INTEGER',
        'user_email': 'ALTER TABLE baixas_estoque ADD COLUMN user_email TEXT',
        'quantidade': 'ALTER TABLE baixas_estoque ADD COLUMN quantidade INTEGER DEFAULT 0',
        'motivo': "ALTER TABLE baixas_estoque ADD COLUMN motivo TEXT DEFAULT 'retirada'",
        'observacao': 'ALTER TABLE baixas_estoque ADD COLUMN observacao TEXT',
        'criado_em': 'ALTER TABLE baixas_estoque ADD COLUMN criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
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
