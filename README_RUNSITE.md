# ValiControl Web Premium

Versão web do ValiControl para rodar no RunSite, substituindo o executável por acesso via navegador.

## O que já vem pronto

- Login e criação de conta trial.
- Dashboard premium e responsivo.
- Cadastro, edição e exclusão de produtos.
- Filtro por vencidos, próximos e OK.
- Busca por produto/código.
- Preenchimento automático por código/GTIN usando `data/dados.xlsx`.
- Índice leve `data/dados.sqlite3` já gerado para não estourar memória no RunSite.
- Importação XLSX/CSV de estoque com validade e quantidade.
- Exportação XLSX/CSV.
- Plano Trial e bloqueio de limite.
- Upgrade PRO com PIX via Asaas.
- Webhook Asaas em `/webhook/asaas/`.
- Comando manual para ativar PRO.
- Scripts `build.sh`, `runsite_start.sh` e `Procfile` prontos.

## RunSite

Build Command:

```bash
bash build.sh
```

Start Command:

```bash
bash runsite_start.sh
```

Porta: deixe automático/em branco. O start usa `$PORT`.

## Variáveis obrigatórias

```env
SECRET_KEY=gere_uma_chave_segura
DATABASE_URL=sua_url_postgresql_ou_neon
ASAAS_API_KEY=sua_chave_asaas
ALLOWED_HOSTS=valicontrol-web.runsite.app,.runsite.app,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://valicontrol-web.runsite.app,https://*.runsite.app
DEBUG=False
RUNSITE=True
```

## Webhook Asaas

Configure no Asaas:

```text
https://valicontrol-web.runsite.app/webhook/asaas/
```

Eventos importantes:

```text
PAYMENT_RECEIVED
PAYMENT_CONFIRMED
```

## Diagnóstico

```bash
python manage.py diagnosticar_runsite
python manage.py indexar_catalogo --skip-if-ready
python manage.py shell -c "from core.services import carregar_catalogo_produtos; c=carregar_catalogo_produtos(); print(len(c)); print(c.get('7898082113571'))"
```

## Ativar conta manualmente

```bash
python manage.py ativar_pro usuario@email.com --dias 30
```


Cadastro protegido por código:
CADASTRO_AUTORIZACAO_OBRIGATORIA=True
CADASTRO_EMAIL_TRAVADO=thiago01268230@gmail.com
CADASTRO_AUTORIZACAO_EMAIL=thiago01268230@gmail.com
CADASTRO_AUTORIZACAO_WHATSAPP=55DDDNUMERO
CADASTRO_CODIGO_EXPIRA_MINUTOS=30
BREVO_API_KEY=sua_chave_api_brevo
BREVO_SENDER_EMAIL=canalescanorff6@gmail.com
BREVO_SENDER_NAME=ValiControl Web
DEFAULT_FROM_EMAIL=ValiControl Web <canalescanorff6@gmail.com>

Fluxo: o usuário solicita o código, o código chega no e-mail autorizado do administrador, e a conta só é criada quando esse código for informado na tela de cadastro.

## Otimização de imagens

A tela de login/cadastro foi ajustada para usar um logotipo estático feito em CSS, sem carregar a imagem grande do logo. O arquivo `static/img/logo.png` também foi substituído por uma versão leve para evitar lentidão caso alguma página antiga ainda o solicite.
