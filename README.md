# valicontrol-backend

Cadastro protegido por código:
CADASTRO_AUTORIZACAO_OBRIGATORIA=True
CADASTRO_AUTORIZACAO_EMAIL=seu_email_de_administrador
CADASTRO_AUTORIZACAO_WHATSAPP=55DDDNUMERO
CADASTRO_CODIGO_EXPIRA_MINUTOS=30
BREVO_API_KEY=sua_chave_api_brevo
BREVO_SENDER_EMAIL=email_verificado_na_brevo
BREVO_SENDER_NAME=ValiControl Web
DEFAULT_FROM_EMAIL=ValiControl Web <email_verificado_na_brevo>

Fluxo: o usuário solicita o código, o código chega no e-mail autorizado do administrador, e a conta só é criada quando esse código for informado na tela de cadastro.
