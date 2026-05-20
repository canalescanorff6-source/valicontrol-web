from datetime import datetime, date, timedelta
import json

from django.contrib import messages
from django.db import connection
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import Produto
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


def registrar_view(request):
    if request.session.get('email'):
        return redirect('core:dashboard')

    context = {
        'cadastro_autorizacao_obrigatoria': True,
        'cadastro_autorizacao_email': getattr(settings, 'CADASTRO_AUTORIZACAO_EMAIL', 'thiago01268230@gmail.com'),
        'cadastro_whatsapp_link': whatsapp_authorization_link(),
        'codigo_solicitado_para': '',
    }

    if request.method == 'POST':
        acao = request.POST.get('acao', 'criar_conta')
        email = request.POST.get('email', '')
        senha = request.POST.get('senha', '')
        confirmar = request.POST.get('confirmar', '')
        codigo = request.POST.get('codigo_autorizacao', '')
        context['codigo_solicitado_para'] = email
        context['cadastro_whatsapp_link'] = whatsapp_authorization_link(email)

        if acao == 'solicitar_codigo':
            resultado, erro = solicitar_codigo_autorizacao(email, get_client_ip(request))
            if erro:
                messages.error(request, erro)
            else:
                context['codigo_solicitado_para'] = resultado['email']
                context['cadastro_whatsapp_link'] = resultado.get('whatsapp_link') or context['cadastro_whatsapp_link']
                messages.success(request, 'Código enviado para o e-mail autorizado do administrador.')
                messages.info(request, 'Agora peça o código ao administrador pelo e-mail ou WhatsApp autorizado.')
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
            if quantidade_int < 0:
                raise ValueError
        except Exception:
            messages.error(request, 'Quantidade inválida.')
            return redirect('core:produtos')

        Produto.objects.create(
            codigo=codigo,
            nome=nome,
            validade=validade,
            quantidade=quantidade_int,
            tipo_qtd=tipo_qtd,
            user_email=conta.email,
        )
        registrar_log(conta.email, 'produto_adicionado_web')
        messages.success(request, 'Produto adicionado com sucesso.')
        return redirect('core:produtos')

    busca = (request.GET.get('q') or '').strip()
    filtro = (request.GET.get('status') or 'todos').strip().lower()

    qs = Produto.objects.filter(user_email=conta.email)
    if busca:
        qs = qs.filter(Q(codigo__icontains=busca) | Q(nome__icontains=busca))

    hoje = date.today().isoformat()
    limite_proximo = (date.today() + timedelta(days=settings.VENCIMENTO_PROXIMO_DIAS)).isoformat()
    if filtro == 'vencido':
        qs = qs.filter(validade__lt=hoje)
    elif filtro == 'proximo':
        qs = qs.filter(validade__gte=hoje, validade__lte=limite_proximo)
    elif filtro == 'ok':
        qs = qs.filter(validade__gt=limite_proximo)

    qs = qs.order_by('validade', 'nome')
    paginator = Paginator(qs, 50)
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

        try:
            datetime.strptime(validade, '%Y-%m-%d')
            quantidade_int = int(float(quantidade))
            if quantidade_int < 0:
                raise ValueError
        except Exception:
            messages.error(request, 'Confira a validade e a quantidade.')
            return redirect('core:editar_produto', produto_id=produto.id)

        produto.codigo = codigo
        produto.nome = nome
        produto.validade = validade
        produto.quantidade = quantidade_int
        produto.tipo_qtd = tipo_qtd
        produto.save()
        registrar_log(conta.email, 'produto_editado_web')
        messages.success(request, 'Produto atualizado.')
        return redirect('core:produtos')

    return render(request, 'core/editar_produto.html', {
        'conta': conta,
        'produto': produto,
        'tipos_qtd': ['Un', 'Cx', 'Kg', 'L', 'Pct', 'Fardo'],
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
    codigo = request.GET.get('codigo', '')
    data = buscar_catalogo(codigo)
    if not data:
        return JsonResponse({'found': False})
    return JsonResponse({'found': True, **data})


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


@require_login
def pagar_view(request):
    conta = get_conta_por_email(request.session.get('email'))
    pagamento = None

    if request.method == 'POST':
        pagamento, erro = criar_pagamento_pix(conta.email)
        if erro:
            messages.error(request, erro)
        else:
            messages.success(request, 'PIX gerado com sucesso.')

    return render(request, 'core/pagar.html', {
        'conta': conta,
        'pagamento': pagamento,
        'stats': estatisticas(conta),
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
    status = {'ok': True, 'database': connection.vendor, 'asaas_configurado': bool(settings.ASAAS_API_KEY)}
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception as exc:
        status = {'ok': False, 'erro': str(exc)}
    return JsonResponse(status, status=200 if status.get('ok') else 500)
