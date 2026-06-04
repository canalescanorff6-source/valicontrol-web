# ValiControl Web - RunSite

Projeto web para controle de validades, com cadastro protegido por código, base de produtos local e pagamento PRO por PIX manual.

## Configuração no RunSite

**Build Command**

```bash
bash build.sh
```

**Start Command**

```bash
bash runsite_start.sh
```

A porta pode ficar automática, pois o projeto usa `$PORT`.

## Variáveis obrigatórias

```env
SECRET_KEY=gere_uma_chave_grande
DEBUG=False
RUNSITE=True
ALLOWED_HOSTS=valicontrol-web.runsite.app,.runsite.app,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://valicontrol-web.runsite.app,https://*.runsite.app
DATABASE_URL=sua_url_do_neon
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
WEB_CONCURRENCY=1
GUNICORN_THREADS=2
```

## Cadastro por código

```env
CADASTRO_EMAIL_TRAVADO=thiago01268230@gmail.com
CADASTRO_AUTORIZACAO_EMAIL=thiago01268230@gmail.com
CADASTRO_AUTORIZACAO_OBRIGATORIA=True
CADASTRO_AUTORIZACAO_WHATSAPP=5598996127032
CADASTRO_CODIGO_EXPIRA_MINUTOS=15
```

## Brevo

```env
BREVO_API_KEY=sua_chave_api_brevo
BREVO_SENDER_EMAIL=canalescanorff6@gmail.com
BREVO_SENDER_NAME=ValiControl Web
DEFAULT_FROM_EMAIL=ValiControl Web <canalescanorff6@gmail.com>
EMAIL_BACKEND=core.email_backends.BrevoEmailBackend
EMAIL_TIMEOUT=20
```

`BREVO_SENDER_EMAIL` é quem envia. `CADASTRO_EMAIL_TRAVADO` é quem recebe o código.

## PIX manual sem Asaas

```env
PAGAMENTO_MODO=manual_pix
PIX_VALOR=100.00
PIX_CHAVE=sua_chave_pix
PIX_TITULAR=Seu nome ou empresa
PIX_WHATSAPP=5598996127032
PAGAMENTO_DESCRICAO=Plano ValiControl PRO
```

Após conferir o comprovante, ative o PRO:

```bash
python manage.py ativar_pro cliente@validade.app --dias 30
```

## Diagnóstico

```bash
python manage.py diagnosticar_runsite
python manage.py verificar_cadastro_codigo
python manage.py diagnosticar_email
python manage.py diagnosticar_email --teste teste@validade.app
```
