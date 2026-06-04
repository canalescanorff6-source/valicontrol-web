from datetime import datetime, date, timedelta
import json
import re
import urllib.parse

from django.contrib import messages
from django.db import connection
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from openpyxl import Workbook
from io import BytesIO

from .models import Produto, BaixaEstoque, Conta
from .services import (
    autenticar,
    buscar_catalogo,
    calcular_dias_restantes,
    criar_conta,
    criar_pagamento_pix,
    estatisticas,
    exportar_produtos_csv,
    exportar_produtos_xlsx,
    formatar_data_br,
    get_client_ip,
    get_conta_por_email,
    importar_produtos_de_planilha,
    montar_produto_dict,
    pode_adicionar_produto,
    produto_status,
    produtos_do_usuario,
    registrar_log,
    ativar_usuario,
    solicitar_codigo_autorizacao,
    validar_codigo_autorizacao,
    marcar_codigo_autorizacao_usado,
    whatsapp_authorization_link,
    obter_config,
    salvar_config,
)


def require_login(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('email'):
            messages.warning(request, 'Entre para continuar.')
            return redirect('core:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def login_view(request):
    if request.session.get('email'):
        return redirect('core:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '')
        senha = request.POST.get('senha', '')
        conta, erro = autenticar(email, senha)
        if erro:
            messages.error(request, erro)
        else:
            request.session['email'] = conta.email
            request.session['usuario'] = conta.email.split('@')[0]
            messages.success(request, 'Login realizado com sucesso.')
            return redirect('core:dashboard')

    return render(request, 'core/login.html')


def _email_destino_codigo() -> str:
    """E-mail administrativo que recebe o código.

    Esse e-mail fica travado na tela apenas como DESTINO do código.
    A conta que será criada continua sendo digitada pelo usuário.
    """
    valor = (
        getattr(settings, 'CADASTRO_EMAIL_TRAVADO', '')
        or getattr(settings, 'CADASTRO_DESTINATARIO_CODIGO', '')
        or getattr(settings, 'CADASTRO_AUTORIZACAO_EMAIL', '')
        or 'thiago01268230@gmail.com'
    )
    for parte in str(valor).replace(';', ',').replace(' ', ',').split(','):
        parte = parte.strip()
        if parte:
            return parte
    return 'thiago01268230@gmail.com'


def registrar_view(request):
    if request.session.get('email'):
        return redirect('core:dashboard')

    email_destino_codigo = _email_destino_codigo()
    email_informado = ''
    context = {
        'cadastro_autorizacao_obrigatoria': True,
        'cadastro_autorizacao_email': email_destino_codigo,
        'cadastro_email_travado': email_destino_codigo,
        'email_destino_codigo': email_destino_codigo,
        'email_informado': email_informado,
        'cadastro_whatsapp_link': whatsapp_authorization_link(email_informado),
        'codigo_solicitado_para': email_informado,
    }

    if request.method == 'POST':
        acao = request.POST.get('acao', 'criar_conta')
        # Agora somente o e-mail que RECEBE o código fica travado.
        # O e-mail da CONTA continua editável e é o valor usado para validar o código.
        email = request.POST.get('email', '')
        senha = request.POST.get('senha', '')
        confirmar = request.POST.get('confirmar', '')
        codigo = request.POST.get('codigo_autorizacao', '')
        context['email_informado'] = email
        context['codigo_solicitado_para'] = email
        context['cadastro_whatsapp_link'] = whatsapp_authorization_link(email)

        if acao == 'solicitar_codigo':
            resultado, erro = solicitar_codigo_autorizacao(email, get_client_ip(request))
            if erro:
                messages.error(request, erro)
            else:
                context['codigo_solicitado_para'] = resultado.get('email') or email
                context['email_informado'] = resultado.get('email') or email
                context['cadastro_whatsapp_link'] = resultado.get('whatsapp_link') or context['cadastro_whatsapp_link']
                messages.success(request, 'Código enviado para o administrador autorizado: %s.' % email_destino_codigo)
                messages.info(request, 'Depois de receber o código, use o mesmo usuário/e-mail informado para finalizar o cadastro.')
            return _render_registrar_no_cache(request, context)

        if senha != confirmar:
            messages.error(request, 'As senhas não coincidem.')
        else:
            autorizacao, erro_codigo = validar_codigo_autorizacao(email, codigo)
            if erro_codigo:
                messages.error(request, erro_codigo)
            else:
                conta, erro = criar_conta(email, senha, get_client_ip(request))
                if erro:
                    messages.error(request, erro)
                else:
                    marcar_codigo_autorizacao_usado(autorizacao.get('id'))
                    request.session['email'] = conta.email
                    request.session['usuario'] = conta.email.split('@')[0]
                    messages.success(request, 'Conta criada com autorização do administrador.')
                    return redirect('core:dashboard')

    return _render_registrar_no_cache(request, context)

def _render_registrar_no_cache(request, context):
    response = render(request, 'core/registrar.html', context)
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def logout_view(request):
    request.session.flush()
    messages.success(request, 'Você saiu da conta.')
    return redirect('core:login')


@require_login
def dashboard_view(request):
    conta = get_conta_por_email(request.session.get('email'))
    if not conta:
        request.session.flush()
        return redirect('core:login')

    stats = estatisticas(conta)
    limite_proximo = (date.today() + timedelta(days=settings.VENCIMENTO_PROXIMO_DIAS)).isoformat()
    vencimentos = []
    for p in Produto.objects.filter(user_email=conta.email, validade__lte=limite_proximo).order_by('validade', 'nome')[:20]:
        status = produto_status(p.validade)
        if status in {'vencido', 'proximo'}:
            vencimentos.append(montar_produto_dict(p))
        if len(vencimentos) >= 10:
            break

    return render(request, 'core/dashboard.html', {
        'conta': conta,
        'stats': stats,
        'vencimentos': vencimentos,
        'trial_restante': calcular_dias_restantes(conta.trial_expira_em),
    })


@require_login
def produtos_view(request):
    conta = get_conta_por_email(request.session.get('email'))
    if not conta:
        request.session.flush()
        return redirect('core:login')

    if request.method == 'POST':
        ok, erro = pode_adicionar_produto(conta)
        if not ok:
            messages.error(request, erro)
            return redirect('core:produtos')

        codigo = request.POST.get('codigo', '').strip()
        nome = request.POST.get('nome', '').strip()
        validade = request.POST.get('validade', '').strip()
        quantidade = request.POST.get('quantidade', '0').strip()
        tipo_qtd = request.POST.get('tipo_qtd', 'Un').strip() or 'Un'
        lote = request.POST.get('lote', '').strip()
        categoria = request.POST.get('categoria', '').strip()
        fornecedor = request.POST.get('fornecedor', '').strip()
        localizacao = request.POST.get('localizacao', '').strip()
        observacao = request.POST.get('observacao', '').strip()
        valor_raw = request.POST.get('valor_unitario', '0').strip().replace(',', '.')

        try:
            datetime.strptime(validade, '%Y-%m-%d')
        except Exception:
            messages.error(request, 'Data de validade inválida.')
            return redirect('core:produtos')

        if not codigo or not nome:
            messages.error(request, 'Preencha código e nome do produto.')
            return redirect('core:produtos')

        try:
            quantidade_int = int(float(quantidade))
            valor_unitario = max(0, float(valor_raw or 0))
            if quantidade_int < 0:
                raise ValueError
        except Exception:
            messages.error(request, 'Quantidade ou valor inválido.')
            return redirect('core:produtos')

        Produto.objects.create(
            codigo=codigo,
            nome=nome,
            validade=validade,
            quantidade=quantidade_int,
            tipo_qtd=tipo_qtd,
            user_email=conta.email,
            lote=lote,
            categoria=categoria,
            fornecedor=fornecedor,
            localizacao=localizacao,
            observacao=observacao,
            valor_unitario=valor_unitario,
            criado_em=datetime.now(),
            atualizado_em=datetime.now(),
        )
        registrar_log(conta.email, 'produto_adicionado_web')
        
        status_novo = produto_status(validade)
        if status_novo == 'vencido':
            messages.warning(request, 'Produto cadastrado, mas a validade informada já está vencida. Confira se a data está correta.')
        elif status_novo == 'proximo':
            messages.warning(request, 'Produto cadastrado. Atenção: ele está próximo do vencimento.')
        else:
            messages.success(request, 'Produto cadastrado com sucesso.')
        return redirect('core:produtos')

    busca = (request.GET.get('q') or '').strip()
    filtro = (request.GET.get('status') or 'todos').strip().lower()

    qs = Produto.objects.filter(user_email=conta.email)
    if busca:
        qs = qs.filter(Q(codigo__icontains=busca) | Q(nome__icontains=busca) | Q(lote__icontains=busca) | Q(categoria__icontains=busca) | Q(fornecedor__icontains=busca) | Q(localizacao__icontains=busca))

    hoje = date.today().isoformat()
    limite_proximo = (date.today() + timedelta(days=settings.VENCIMENTO_PROXIMO_DIAS)).isoformat()
    if filtro == 'vencido':
        qs = qs.filter(validade__lt=hoje)
    elif filtro == 'proximo':
        qs = qs.filter(validade__gte=hoje, validade__lte=limite_proximo)
    elif filtro == 'ok':
        qs = qs.filter(validade__gt=limite_proximo)

    qs = qs.order_by('validade', 'nome')
    paginator = Paginator(qs, int(getattr(settings, 'PAGINACAO_PRODUTOS', 25)))
    page_obj = paginator.get_page(request.GET.get('page'))
    produtos = [montar_produto_dict(p) for p in page_obj.object_list]

    stats = estatisticas(conta)
    return render(request, 'core/produtos.html', {
        'conta': conta,
        'stats': stats,
        'produtos': produtos,
        'page_obj': page_obj,
        'busca': busca,
        'filtro': filtro,
        'tipos_qtd': ['Un', 'Cx', 'Kg', 'L', 'Pct', 'Fardo'],
        'categorias_sugeridas': ['Alimentos', 'Bebidas', 'Limpeza', 'Medicamentos', 'Cosméticos', 'Perecíveis', 'Outros'],
        'baixa_motivos': _motivos_baixa(),
    })


@require_login
def editar_produto_view(request, produto_id):
    conta = get_conta_por_email(request.session.get('email'))
    produto = get_object_or_404(Produto, id=produto_id, user_email=conta.email)

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        nome = request.POST.get('nome', '').strip()
        validade = request.POST.get('validade', '').strip()
        quantidade = request.POST.get('quantidade', '0').strip()
        tipo_qtd = request.POST.get('tipo_qtd', 'Un').strip() or 'Un'
        lote = request.POST.get('lote', '').strip()
        categoria = request.POST.get('categoria', '').strip()
        fornecedor = request.POST.get('fornecedor', '').strip()
        localizacao = request.POST.get('localizacao', '').strip()
        observacao = request.POST.get('observacao', '').strip()
        valor_raw = request.POST.get('valor_unitario', '0').strip().replace(',', '.')

        try:
            datetime.strptime(validade, '%Y-%m-%d')
            quantidade_int = int(float(quantidade))
            valor_unitario = max(0, float(valor_raw or 0))
            if quantidade_int < 0:
                raise ValueError
        except Exception:
            messages.error(request, 'Confira a validade, quantidade e valor.')
            return redirect('core:editar_produto', produto_id=produto.id)

        produto.codigo = codigo
        produto.nome = nome
        produto.validade = validade
        produto.quantidade = quantidade_int
        produto.tipo_qtd = tipo_qtd
        produto.lote = lote
        produto.categoria = categoria
        produto.fornecedor = fornecedor
        produto.localizacao = localizacao
        produto.observacao = observacao
        produto.valor_unitario = valor_unitario
        produto.atualizado_em = datetime.now()
        produto.save()
        registrar_log(conta.email, 'produto_editado_web')
        messages.success(request, 'Produto atualizado.')
        return redirect('core:produtos')

    return render(request, 'core/editar_produto.html', {
        'conta': conta,
        'produto': produto,
        'tipos_qtd': ['Un', 'Cx', 'Kg', 'L', 'Pct', 'Fardo'],
        'categorias_sugeridas': ['Alimentos', 'Bebidas', 'Limpeza', 'Medicamentos', 'Cosméticos', 'Perecíveis', 'Outros'],
    })


@require_login
@require_POST
def excluir_produto_view(request, produto_id):
    conta = get_conta_por_email(request.session.get('email'))
    produto = get_object_or_404(Produto, id=produto_id, user_email=conta.email)
    produto.delete()
    registrar_log(conta.email, 'produto_excluido_web')
    messages.success(request, 'Produto excluído.')
    return redirect('core:produtos')


@require_login
def produto_lookup_api(request):
    codigo = (request.GET.get('codigo', '') or '').strip()
    # Evita consulta desnecessária a cada tecla muito curta.
    if len(codigo) < 3:
        response = JsonResponse({'found': False})
        response['Cache-Control'] = 'private, max-age=60'
        return response
    data = buscar_catalogo(codigo)
    if not data:
        response = JsonResponse({'found': False})
        response['Cache-Control'] = 'private, max-age=3600'
        return response
    response = JsonResponse({'found': True, **data})
    # Ajuda o navegador a repetir buscas recentes sem bater de novo no servidor.
    response['Cache-Control'] = 'private, max-age=86400'
    return response


@require_login
def exportar_produtos_view(request, formato):
    conta = get_conta_por_email(request.session.get('email'))
    if formato == 'csv':
        conteudo = exportar_produtos_csv(conta)
        response = HttpResponse(conteudo, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="valicontrol-produtos.csv"'
        return response
    conteudo = exportar_produtos_xlsx(conta)
    response = HttpResponse(conteudo, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="valicontrol-produtos.xlsx"'
    return response


@require_login
@require_POST
def importar_produtos_view(request):
    conta = get_conta_por_email(request.session.get('email'))
    arquivo = request.FILES.get('arquivo')
    if not arquivo:
        messages.error(request, 'Selecione uma planilha XLSX ou CSV.')
        return redirect('core:produtos')
    try:
        criados, erros = importar_produtos_de_planilha(conta, arquivo)
        if criados:
            messages.success(request, f'{criados} produto(s) importado(s) com sucesso.')
        if erros:
            messages.warning(request, ' | '.join(erros))
        if not criados and not erros:
            messages.warning(request, 'Nenhum produto foi importado.')
    except Exception as exc:
        messages.error(request, f'Erro ao importar planilha: {exc}')
    return redirect('core:produtos')


def _whatsapp_link_pagamento(conta_email: str) -> str:
    numero = re.sub(r'\D+', '', obter_config('PIX_WHATSAPP', getattr(settings, 'CADASTRO_AUTORIZACAO_WHATSAPP', '')) or '')
    if not numero:
        return ''
    if not numero.startswith('55') and len(numero) in (10, 11):
        numero = '55' + numero
    msg = (
        'Olá, fiz o pagamento do Plano ValiControl PRO e quero enviar o comprovante.'
        f' Conta: {conta_email}.'
    )
    return f'https://wa.me/{numero}?text={urllib.parse.quote(msg)}'



def _parse_valor_monetario(valor, padrao=100.00):
    try:
        return float(str(valor).strip().replace('.', '').replace(',', '.') if ',' in str(valor) else str(valor).strip())
    except Exception:
        return float(padrao)

def _pagamento_manual_context(conta_email: str) -> dict:
    chave = (obter_config('PIX_CHAVE', '') or '').strip()
    titular = (obter_config('PIX_TITULAR', '') or '').strip()
    pix_configurado = bool(chave and titular)
    return {
        'modo': getattr(settings, 'PAGAMENTO_MODO', 'manual_pix'),
        'chave': chave,
        'titular': titular,
        'pix_configurado': pix_configurado,
        'valor': _parse_valor_monetario(obter_config('PIX_VALOR', getattr(settings, 'PIX_VALOR', 100.00)), 100.00),
        'descricao': obter_config('PAGAMENTO_DESCRICAO', getattr(settings, 'PAGAMENTO_DESCRICAO', 'Plano ValiControl PRO')),
        'observacao': obter_config('PIX_OBSERVACAO', getattr(settings, 'PIX_OBSERVACAO', 'Após o pagamento, envie o comprovante pelo WhatsApp para a equipe liberar o PRO.')),
        'whatsapp_link': _whatsapp_link_pagamento(conta_email),
        'conta_email': conta_email,
    }


@require_login
def pagar_view(request):
    conta = get_conta_por_email(request.session.get('email'))
    pagamento = None
    pagamento_manual = _pagamento_manual_context(conta.email)
    modo_pagamento = getattr(settings, 'PAGAMENTO_MODO', 'manual_pix').lower()

    if request.method == 'POST':
        if modo_pagamento == 'asaas':
            pagamento, erro = criar_pagamento_pix(conta.email)
            if erro:
                messages.error(request, erro)
            else:
                messages.success(request, 'PIX gerado com sucesso pelo Asaas.')
        else:
            messages.success(request, 'Após pagar, envie o comprovante pelo WhatsApp para a equipe liberar o PRO.')

    return render(request, 'core/pagar.html', {
        'conta': conta,
        'pagamento': pagamento,
        'pagamento_manual': pagamento_manual,
        'modo_pagamento': modo_pagamento,
        'stats': estatisticas(conta),
    })


@require_login
def ajuda_view(request):
    conta = get_conta_por_email(request.session.get('email'))
    if not conta:
        request.session.flush()
        return redirect('core:login')
    return render(request, 'core/ajuda.html', {'conta': conta, 'stats': estatisticas(conta)})


def termos_view(request):
    return render(request, 'core/termos.html')


@require_login
def configuracoes_view(request):
    conta_atual = get_conta_por_email(request.session.get('email'))
    if not _is_admin_user(conta_atual.email if conta_atual else ''):
        messages.error(request, 'Área restrita ao administrador do ValiControl.')
        return redirect('core:dashboard')

    chaves = [
        'PIX_CHAVE',
        'PIX_TITULAR',
        'PIX_WHATSAPP',
        'PIX_VALOR',
        'PAGAMENTO_DESCRICAO',
        'PIX_OBSERVACAO',
        'CADASTRO_EMAIL_TRAVADO',
        'CADASTRO_AUTORIZACAO_WHATSAPP',
        'TRIAL_DIAS',
        'TRIAL_LIMITE_PRODUTOS',
        'VENCIMENTO_PROXIMO_DIAS',
    ]

    if request.method == 'POST':
        for chave in chaves:
            salvar_config(chave, request.POST.get(chave, ''))
        registrar_log(conta_atual.email, 'configuracoes_atualizadas')
        messages.success(request, 'Configurações salvas com sucesso.')
        return redirect('core:configuracoes')

    valores = {chave: obter_config(chave, getattr(settings, chave, '')) for chave in chaves}
    return render(request, 'core/configuracoes.html', {
        'conta': conta_atual,
        'valores': valores,
        'stats': estatisticas(conta_atual),
    })


@csrf_exempt
def webhook_asaas_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': True})

    # Se quiser proteger o webhook, configure ASAAS_WEBHOOK_TOKEN e envie esse token no header access_token.
    token_configurado = getattr(settings, 'ASAAS_WEBHOOK_TOKEN', '').strip()
    if token_configurado:
        token_recebido = request.headers.get('access_token') or request.headers.get('asaas-access-token') or ''
        if token_recebido != token_configurado:
            return JsonResponse({'ok': False, 'erro': 'webhook não autorizado'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({'ok': False, 'erro': 'json inválido'}, status=400)

    try:
        evento = data.get('event')
        payment = data.get('payment', {}) or {}
        status = payment.get('status')
        email = payment.get('externalReference')
        payment_id = payment.get('id')

        if payment_id:
            with connection.cursor() as cursor:
                if connection.vendor == 'postgresql':
                    cursor.execute(
                        """
                        INSERT INTO pagamentos (payment_id, email, status, criado_em)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (payment_id)
                        DO UPDATE SET status=EXCLUDED.status, email=EXCLUDED.email
                        """,
                        [payment_id, email, status],
                    )
                else:
                    cursor.execute(
                        "INSERT OR IGNORE INTO pagamentos (payment_id, email, status, criado_em) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)",
                        [payment_id, email, status],
                    )
                    cursor.execute("UPDATE pagamentos SET status=%s, email=%s WHERE payment_id=%s", [status, email, payment_id])

        if evento in ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED'] and status in ['RECEIVED', 'CONFIRMED'] and email:
            ativar_usuario(email)

    except Exception as exc:
        return JsonResponse({'ok': False, 'erro': str(exc)}, status=500)

    return JsonResponse({'ok': True})


def health_view(request):
    status = {'ok': True, 'database': connection.vendor, 'modo_pagamento': getattr(settings, 'PAGAMENTO_MODO', 'manual_pix'), 'brevo_configurado': bool(getattr(settings, 'BREVO_API_KEY', ''))}
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception as exc:
        status = {'ok': False, 'erro': str(exc)}
    return JsonResponse(status, status=200 if status.get('ok') else 500)


def _motivos_baixa():
    return ['Vendido', 'Usado', 'Descartado', 'Perda', 'Doado', 'Retirado por validade', 'Ajuste de estoque']


def _periodo_queryset(qs, periodo: str):
    hoje = date.today()
    hoje_iso = hoje.isoformat()
    if periodo == 'vencidos':
        return qs.filter(validade__lt=hoje_iso)
    if periodo == 'hoje':
        return qs.filter(validade=hoje_iso)
    if periodo in {'7', '15', '30'}:
        limite = (hoje + timedelta(days=int(periodo))).isoformat()
        return qs.filter(validade__gte=hoje_iso, validade__lte=limite)
    if periodo == 'em_dia':
        limite = (hoje + timedelta(days=settings.VENCIMENTO_PROXIMO_DIAS)).isoformat()
        return qs.filter(validade__gt=limite)
    return qs


def _aplicar_busca(qs, busca: str):
    if not busca:
        return qs
    return qs.filter(
        Q(codigo__icontains=busca) |
        Q(nome__icontains=busca) |
        Q(lote__icontains=busca) |
        Q(categoria__icontains=busca) |
        Q(fornecedor__icontains=busca) |
        Q(localizacao__icontains=busca)
    )


@require_login
def vencimentos_view(request):
    conta = get_conta_por_email(request.session.get('email'))
    if not conta:
        request.session.flush()
        return redirect('core:login')

    busca = (request.GET.get('q') or '').strip()
    periodo = (request.GET.get('periodo') or '30').strip().lower()
    qs = Produto.objects.filter(user_email=conta.email)
    qs = _aplicar_busca(qs, busca)
    qs = _periodo_queryset(qs, periodo).order_by('validade', 'nome')
    paginator = Paginator(qs, int(getattr(settings, 'PAGINACAO_PRODUTOS', 25)))
    page_obj = paginator.get_page(request.GET.get('page'))
    produtos = [montar_produto_dict(p) for p in page_obj.object_list]

    return render(request, 'core/vencimentos.html', {
        'conta': conta,
        'stats': estatisticas(conta),
        'produtos': produtos,
        'page_obj': page_obj,
        'busca': busca,
        'periodo': periodo,
        'periodos': [
            ('todos', 'Todos'),
            ('vencidos', 'Vencidos'),
            ('hoje', 'Vencem hoje'),
            ('7', 'Próximos 7 dias'),
            ('15', 'Próximos 15 dias'),
            ('30', 'Próximos 30 dias'),
            ('em_dia', 'Em dia'),
        ],
    })


@require_login
@require_POST
def baixa_produto_view(request, produto_id):
    conta = get_conta_por_email(request.session.get('email'))
    produto = get_object_or_404(Produto, id=produto_id, user_email=conta.email)
    try:
        quantidade = int(float((request.POST.get('quantidade_baixa') or '0').replace(',', '.')))
        if quantidade <= 0:
            raise ValueError
    except Exception:
        messages.error(request, 'Informe uma quantidade válida para dar baixa.')
        return redirect(request.POST.get('next') or 'core:produtos')

    motivo = request.POST.get('motivo_baixa', 'Retirada').strip() or 'Retirada'
    observacao = request.POST.get('observacao_baixa', '').strip()
    quantidade_final = max(0, (produto.quantidade or 0) - quantidade)
    quantidade_real = min(quantidade, produto.quantidade or 0)
    produto.quantidade = quantidade_final
    produto.atualizado_em = datetime.now()
    produto.save(update_fields=['quantidade', 'atualizado_em'])
    BaixaEstoque.objects.create(
        produto_id=produto.id,
        user_email=conta.email,
        quantidade=quantidade_real,
        motivo=motivo,
        observacao=observacao,
        criado_em=datetime.now(),
    )
    registrar_log(conta.email, f'baixa_estoque_{produto.id}_{quantidade_real}')
    messages.success(request, f'Baixa registrada: {quantidade_real} {produto.tipo_qtd or "Un"} de {produto.nome}.')
    return redirect(request.POST.get('next') or 'core:produtos')


@require_login
def relatorios_view(request):
    conta = get_conta_por_email(request.session.get('email'))
    if not conta:
        request.session.flush()
        return redirect('core:login')
    produtos = list(Produto.objects.filter(user_email=conta.email).order_by('validade', 'nome'))
    itens = [montar_produto_dict(p) for p in produtos]
    stats = estatisticas(conta)

    por_categoria = {}
    valor_risco = 0.0
    for item in itens:
        cat = item['categoria'] or 'Sem categoria'
        por_categoria.setdefault(cat, {'categoria': cat, 'total': 0, 'vencidos': 0, 'proximos': 0, 'valor_risco': 0.0})
        por_categoria[cat]['total'] += 1
        if item['status'] == 'vencido':
            por_categoria[cat]['vencidos'] += 1
            por_categoria[cat]['valor_risco'] += item['valor_total']
            valor_risco += item['valor_total']
        elif item['status'] == 'proximo':
            por_categoria[cat]['proximos'] += 1
            por_categoria[cat]['valor_risco'] += item['valor_total']
            valor_risco += item['valor_total']

    baixas = list(BaixaEstoque.objects.filter(user_email=conta.email).order_by('-criado_em')[:25])
    total_baixado = sum(int(b.quantidade or 0) for b in baixas)

    return render(request, 'core/relatorios.html', {
        'conta': conta,
        'stats': stats,
        'valor_risco': round(valor_risco, 2),
        'por_categoria': sorted(por_categoria.values(), key=lambda x: (-x['vencidos'], -x['proximos'], x['categoria'])),
        'baixas': baixas,
        'total_baixado': total_baixado,
    })


@require_login
def exportar_relatorio_view(request):
    conta = get_conta_por_email(request.session.get('email'))
    wb = Workbook()
    ws = wb.active
    ws.title = 'Relatório'
    ws.append(['Produto', 'Código', 'Lote', 'Categoria', 'Fornecedor', 'Localização', 'Validade', 'Quantidade', 'Tipo', 'Valor total', 'Status'])
    for produto in Produto.objects.filter(user_email=conta.email).order_by('validade', 'nome'):
        item = montar_produto_dict(produto)
        ws.append([item['nome'], item['codigo'], item['lote'], item['categoria'], item['fornecedor'], item['localizacao'], item['validade'], item['quantidade'], item['tipo_qtd'], item['valor_total'], item['status_label']])
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 52)
    bio = BytesIO()
    wb.save(bio)
    response = HttpResponse(bio.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="valicontrol-relatorio.xlsx"'
    return response


@require_login
def etiquetas_view(request):
    conta = get_conta_por_email(request.session.get('email'))
    if not conta:
        request.session.flush()
        return redirect('core:login')
    busca = (request.GET.get('q') or '').strip()
    ids = request.GET.getlist('id')
    qs = Produto.objects.filter(user_email=conta.email)
    if ids:
        qs = qs.filter(id__in=ids)
    qs = _aplicar_busca(qs, busca).order_by('validade', 'nome')[:80]
    produtos = [montar_produto_dict(p) for p in qs]
    return render(request, 'core/etiquetas.html', {
        'conta': conta,
        'produtos': produtos,
        'busca': busca,
        'stats': estatisticas(conta),
    })


def _is_admin_user(email: str) -> bool:
    email = (email or '').strip().lower()
    admin_raw = getattr(settings, 'ADMIN_EMAILS', '') or getattr(settings, 'CRIADOR_ADMIN_EMAILS', '') or getattr(settings, 'CADASTRO_EMAIL_TRAVADO', '') or getattr(settings, 'CADASTRO_AUTORIZACAO_EMAIL', '')
    admins = {item.strip().lower() for item in re.split(r'[,;\s]+', str(admin_raw)) if item.strip()}
    return bool(email and email in admins)


@require_login
def admin_contas_view(request):
    conta_atual = get_conta_por_email(request.session.get('email'))
    if not _is_admin_user(conta_atual.email if conta_atual else ''):
        messages.error(request, 'Área restrita ao administrador do ValiControl.')
        return redirect('core:dashboard')
    busca = (request.GET.get('q') or '').strip()
    qs = Conta.objects.all().order_by('-id')
    if busca:
        qs = qs.filter(email__icontains=busca)
    paginator = Paginator(qs, int(getattr(settings, 'PAGINACAO_PRODUTOS', 25)))
    page_obj = paginator.get_page(request.GET.get('page'))
    contas = []
    for conta in page_obj.object_list:
        contas.append({
            'conta': conta,
            'stats': estatisticas(conta),
            'produtos': Produto.objects.filter(user_email=conta.email).count(),
        })
    total_contas = Conta.objects.count()
    contas_pro = Conta.objects.filter(ativo=1).count()
    contas_trial = max(0, total_contas - contas_pro)
    total_produtos = Produto.objects.count()
    return render(request, 'core/admin_contas.html', {
        'conta': conta_atual,
        'contas': contas,
        'page_obj': page_obj,
        'busca': busca,
        'admin_stats': {
            'total_contas': total_contas,
            'contas_pro': contas_pro,
            'contas_trial': contas_trial,
            'total_produtos': total_produtos,
        },
    })


@require_login
@require_POST
def admin_ativar_pro_view(request, conta_id):
    conta_atual = get_conta_por_email(request.session.get('email'))
    if not _is_admin_user(conta_atual.email if conta_atual else ''):
        messages.error(request, 'Área restrita ao administrador do ValiControl.')
        return redirect('core:dashboard')
    conta = get_object_or_404(Conta, id=conta_id)
    dias = int(request.POST.get('dias') or 30)
    ativar_usuario(conta.email, dias=dias)
    messages.success(request, f'Conta {conta.email} ativada como PRO por {dias} dias.')
    return redirect('core:admin_contas')


@require_login
@require_POST
def admin_bloquear_view(request, conta_id):
    conta_atual = get_conta_por_email(request.session.get('email'))
    if not _is_admin_user(conta_atual.email if conta_atual else ''):
        messages.error(request, 'Área restrita ao administrador do ValiControl.')
        return redirect('core:dashboard')
    conta = get_object_or_404(Conta, id=conta_id)
    conta.ativo = 0
    conta.plano = 'trial'
    conta.save(update_fields=['ativo', 'plano'])
    messages.success(request, f'Conta {conta.email} voltou para TRIAL.')
    return redirect('core:admin_contas')
