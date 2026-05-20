from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('registrar/', views.registrar_view, name='registrar'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('produtos/', views.produtos_view, name='produtos'),
    path('produtos/importar/', views.importar_produtos_view, name='importar_produtos'),
    path('produtos/exportar/<str:formato>/', views.exportar_produtos_view, name='exportar_produtos'),
    path('produtos/<int:produto_id>/editar/', views.editar_produto_view, name='editar_produto'),
    path('produtos/<int:produto_id>/excluir/', views.excluir_produto_view, name='excluir_produto'),
    path('api/produto-lookup/', views.produto_lookup_api, name='produto_lookup_api'),
    path('pagar/', views.pagar_view, name='pagar'),
    path('webhook/asaas/', views.webhook_asaas_view, name='webhook_asaas'),
    path('health/', views.health_view, name='health'),
]
