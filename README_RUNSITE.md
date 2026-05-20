# ValiControl Web Premium

Versão web do ValiControl para rodar no RunSite, substituindo o executável por acesso via navegador.

## O que já vem pronto

- Login e criação de conta trial.
- Dashboard premium e responsivo.
- Cadastro, edição e exclusão de produtos.
- Filtro por vencidos, próximos e OK.
- Busca por produto/código.
- Preenchimento automático por código/GTIN usando `data/dados.xlsx`.
- Importação XLSX/CSV de produtos.
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

## Variáveis obrigatórias

```env
SECRET_KEY=gere_uma_chave_segura
DATABASE_URL=sua_url_postgresql
ASAAS_API_KEY=sua_chave_asaas
ALLOWED_HOSTS=seu-app.runsite.app,.runsite.app,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://seu-app.runsite.app,https://*.runsite.app
DEBUG=False
RUNSITE=True
```

## Webhook Asaas

Configure no Asaas:

```text
https://seu-app.runsite.app/webhook/asaas/
```

Eventos importantes:

```text
PAYMENT_RECEIVED
PAYMENT_CONFIRMED
```

## Diagnóstico

```bash
python manage.py diagnosticar_runsite
```

## Ativar conta manualmente

```bash
python manage.py ativar_pro usuario@email.com --dias 30
```
