from django.db import models


class Conta(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.TextField(unique=True)
    senha = models.TextField()
    token = models.TextField(null=True, blank=True)
    criado_em = models.DateTimeField(null=True, blank=True)
    trial_expira_em = models.DateTimeField(null=True, blank=True)
    ativo = models.IntegerField(default=0)
    device_id = models.TextField(null=True, blank=True)
    plano = models.TextField(default='trial')
    ip = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'users'

    def __str__(self):
        return self.email


class Produto(models.Model):
    id = models.AutoField(primary_key=True)
    codigo = models.TextField(null=True, blank=True)
    nome = models.TextField(null=True, blank=True)
    validade = models.TextField(null=True, blank=True)
    quantidade = models.IntegerField(default=0)
    tipo_qtd = models.TextField(default='Un')
    user_email = models.TextField()
    lote = models.TextField(null=True, blank=True)
    categoria = models.TextField(null=True, blank=True)
    fornecedor = models.TextField(null=True, blank=True)
    localizacao = models.TextField(null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)
    valor_unitario = models.FloatField(default=0)
    criado_em = models.DateTimeField(null=True, blank=True)
    atualizado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'produtos'

    def __str__(self):
        return f'{self.nome} ({self.codigo})'


class Log(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.TextField(null=True, blank=True)
    acao = models.TextField(null=True, blank=True)
    criado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'logs'


class Pagamento(models.Model):
    id = models.AutoField(primary_key=True)
    payment_id = models.TextField(unique=True)
    email = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    criado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pagamentos'


class BaixaEstoque(models.Model):
    id = models.AutoField(primary_key=True)
    produto_id = models.IntegerField()
    user_email = models.TextField()
    quantidade = models.IntegerField(default=0)
    motivo = models.TextField(default='retirada')
    observacao = models.TextField(null=True, blank=True)
    criado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'baixas_estoque'
