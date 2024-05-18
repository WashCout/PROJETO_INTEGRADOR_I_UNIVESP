from django.urls import path
from . import views

urlpatterns = [
    path('api/estoque/', views.estoque_api, name='api_estoque'),
    path('estoque/', views.estoque, name='estoque'),
    path('finalizar-compra/', views.finalizar_compra, name='finalizar_compra'),
    path('pedidos/', views.pedidos, name='pedidos'),
    path('atualizar-status/<int:venda_id>/', views.atualizar_status, name='atualizar_status'),
    path('verificar-pedido/', views.verificar_pedido, name='verificar_pedido'),
    path('produtos-mais-pedidos/', views.produtos_mais_pedidos, name='produtos_mais_pedidos'),
    
]
