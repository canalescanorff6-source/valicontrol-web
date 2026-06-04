from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('registrar/', views.registrar_view, name='registrar'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('produtos/', views.produtos_view, name='produtos'),
    path('produtos/importar/', views.importar_produtos_view, name='importar_produtos'),
    path('produtos/exportar/<str:formato>/', views.exportar_produtos_view, name='exportar_produtos'),
    path('produtos/<int:produto_id>/editar/', views.editar_produto_view, name='editar_produto'),
    path('produtos/<int:produto_id>/excluir/', views.excluir_produto_view, name='excluir_produto'),
    path('produtos/<int:produto_id>/baixa/', views.baixa_produto_view, name='baixa_produto'),
    path('vencimentos/', views.vencimentos_view, name='vencimentos'),
    path('relatorios/', views.relatorios_view, name='relatorios'),
    path('relatorios/exportar/', views.exportar_relatorio_view, name='exportar_relatorio'),
    path('etiquetas/', views.etiquetas_view, name='etiquetas'),
    path('admin-contas/', views.admin_contas_view, name='admin_contas'),
    path('configuracoes/', views.configuracoes_view, name='configuracoes'),
    path('ajuda/', views.ajuda_view, name='ajuda'),
    path('termos/', views.termos_view, name='termos'),
    path('admin-contas/<int:conta_id>/ativar-pro/', views.admin_ativar_pro_view, name='admin_ativar_pro'),
    path('admin-contas/<int:conta_id>/bloquear/', views.admin_bloquear_view, name='admin_bloquear'),
    path('api/produto-lookup/', views.produto_lookup_api, name='produto_lookup_api'),
    path('pagar/', views.pagar_view, name='pagar'),
    path('webhook/asaas/', views.webhook_asaas_view, name='webhook_asaas'),
    path('health/', views.health_view, name='health'),
]
