from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.mail import send_mail
from lojistas.models import Estoque, Vendas, Lojista
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from django.db import transaction

@login_required
def estoque_api(request):
    try:
        estoques = Estoque.objects.all().select_related('produto')
        estoques_list = []
        for estoque in estoques:
            estoques_list.append({
                'codigo': estoque.codigo,
                'nome_produto': estoque.produto.nome_produto,
                'categoria': estoque.produto.get_categoria_display(),
                'subcategoria': estoque.produto.get_subcategoria_display(),
                'quantidade': estoque.quantidade,
                'valor': str(estoque.valor)
            })
        return JsonResponse(estoques_list, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def estoque(request):
    try:
        lojista = request.user
        return render(request, 'estoque.html', {'lojista': lojista})
    except Exception as e:
        return redirect('index')

@login_required
def verificar_pedido(request):
    lojista = request.user
    tem_pedido_em_andamento = Vendas.objects.filter(lojista__user=lojista, processo='em_andamento').exists()
    return JsonResponse({'tem_pedido_em_andamento': tem_pedido_em_andamento})

@login_required
@transaction.atomic
def finalizar_compra(request):
    if request.method == 'POST':
        try:
            pedido_data = json.loads(request.POST.get('pedido'))
            lojista = request.user
            tem_pedido_em_andamento = request.POST.get('tem_pedido_em_andamento') == 'true'

            pedido_str = ''
            valor_total_pedido = 0

            # Lista para armazenar atualizações de estoque pendentes
            updates = []

            for item in pedido_data:
                valor_total_item = float(item['valor_total'])
                valor_unitario = float(item['valor_unitario'])
                quantidade = int(item['quantidade'])
                nome_produto = item['nome_produto']

                # Verificar e preparar atualização do estoque
                produto_estoque = Estoque.objects.select_for_update().get(produto__nome_produto=nome_produto)
                if produto_estoque.quantidade >= quantidade:
                    updates.append((produto_estoque, quantidade))
                else:
                    return JsonResponse({'status': 'error', 'message': f'Quantidade insuficiente em estoque para {nome_produto}'}, status=400)

                pedido_str += f"Produto: {nome_produto}, Quantidade: {quantidade}, Valor Unitário: R$ {valor_unitario:.2f}, Valor Total: R$ {valor_total_item:.2f}\n"
                valor_total_pedido += valor_total_item

            pedido_str += f"\nValor Total do Pedido: R$ {valor_total_pedido:.2f}"

            # Aplicar atualizações de estoque
            for produto_estoque, quantidade in updates:
                produto_estoque.quantidade -= quantidade
                produto_estoque.save()

            # Criar registro de venda
            venda = Vendas(
                lojista=Lojista.objects.get(user=lojista),
                detalhes=json.dumps(pedido_data),
                processo='em_andamento'
            )
            venda.save()

            # Enviar email (opcional)
            email_body = f"Um novo pedido foi realizado pelo lojista {lojista.username}:\n\n{pedido_str}"
            if tem_pedido_em_andamento:
                email_body = f"Este pedido foi enviado, mas já havia outra solicitação em andamento, entre em contato com o lojista ({lojista.username}) para não haver irregularidades. Telefone: {lojista.lojista.telefone}\n\n" + email_body

            send_mail(
                'Novo Pedido de Estoque',
                email_body,
                'univesp.pi005@gmail.com',
                ['univesp.pi005@gmail.com'],
                fail_silently=False,
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def pedidos(request):
    try:
        lojista = request.user
        vendas = Vendas.objects.filter(lojista__user=lojista)
        return render(request, 'pedidos.html', {'lojista': lojista, 'vendas': vendas})
    except Exception as e:
        return redirect('index')

@login_required
def atualizar_status(request, venda_id):
    if request.method == 'POST':
        venda = get_object_or_404(Vendas, id=venda_id)
        novo_status = request.POST.get('status')

        # Atualizar status
        venda.processo = novo_status
        venda.save()

        # Atualizar estoque se o pedido for cancelado
        if novo_status == 'cancelado':
            venda.atualizar_estoque_cancelar()

        return redirect('pedidos')
    return JsonResponse({'status': 'error', 'message': 'Método inválido'}, status=400)
