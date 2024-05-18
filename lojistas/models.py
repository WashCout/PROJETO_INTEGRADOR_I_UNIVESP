from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, EmailValidator, MinValueValidator
import json

class Produto(models.Model):
    CATEGORIAS = [
        ('picole', 'Picolé'),
        ('massa', 'Massa'),
        ('pote', 'Pote'),
    ]
    SUBCATEGORIAS = [
        ('PA', 'Paleta'),
        ('PT', 'Picolé Tradicional'),
        ('PG', 'Picolé Especial'),
        ('PK', 'Picolé Kids'),
        ('M5L', 'Massa 5 Litros'),
        ('MA', 'Massa Açaí'),
        ('MT', 'Massa Tradicional'),
        ('ME', 'Massa Especial'),
        ('PMA', 'Pote Massa Açaí'),
        ('PMT', 'Pote Massa Tradicional'),
        ('PME', 'Pote Massa Especial'),
    ]

    codigo = models.IntegerField(default=0)
    nome_produto = models.CharField(max_length=50, default='sorvete', verbose_name="Nome do Produto", primary_key=True)
    descricao = models.TextField(verbose_name="Descrição")
    categoria = models.CharField(
        max_length=30, 
        choices=CATEGORIAS, 
        default='picole', 
        verbose_name="Categoria"
    )
    subcategoria = models.CharField(
        max_length=30, 
        choices=SUBCATEGORIAS, 
        default='PA', 
        verbose_name="Subcategoria"
    )

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

    def __str__(self):
        return f"{self.nome_produto} ({self.get_categoria_display()})"

class Lojista(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Usuário Associado"
    )
    nome_loja = models.CharField(
        max_length=30, 
        primary_key=True, 
        verbose_name="Nome da Loja"
    )
    endereco = models.TextField(
        verbose_name="Endereço"
    )
    telefone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Número de telefone deve ser inserido no formato: '+999999999'. Até 15 dígitos."
    )
    telefone = models.CharField(
        validators=[telefone_regex], 
        max_length=17, 
        verbose_name="Telefone"
    )
    email = models.EmailField(
        max_length=100,
        validators=[EmailValidator()],
        verbose_name="Email"
    )

    class Meta:
        verbose_name = "Lojista"
        verbose_name_plural = "Lojistas"

    def __str__(self):
        return f"{self.nome_loja}"

class Estoque(models.Model):
    codigo = models.IntegerField(default=0)
    produto = models.ForeignKey(
        'Produto', 
        on_delete=models.CASCADE, 
        related_name='estoques', 
        verbose_name="Produto"
    )
    quantidade = models.IntegerField(
        default=30, 
        validators=[MinValueValidator(0)], 
        verbose_name="Quantidade"
    )
    valor = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Valor Unitário"
    )
    class Meta:
        verbose_name = 'Item de Estoque'
        verbose_name_plural = 'Itens de Estoque'

    def __str__(self):
        return f"{self.produto.nome_produto} - Quantidade: {self.quantidade}, Valor: R${self.valor}"

    def valor_total(self):
        return self.quantidade * self.valor

class Vendas(models.Model):
    PROCESSO_CHOICES = [
        ('realizado', 'Realizado'),
        ('nao_realizado', 'Não Realizado'),
        ('em_andamento', 'Em Andamento'),
        ('cancelado', 'Cancelado'),
    ]

    processo = models.CharField(
        max_length=20,
        choices=PROCESSO_CHOICES,
        default='em_andamento',
        help_text='Estado do processo da reserva'
    )
    lojista = models.ForeignKey(Lojista, on_delete=models.CASCADE, help_text='Lojista responsável pela reserva')
    data = models.DateTimeField(default=timezone.now, help_text='Data e hora da realização da reserva')
    detalhes = models.TextField(help_text='Detalhes do pedido', default='Não há solicitação de reserva de produtos')

    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'

    @property
    def valor_total(self):
        detalhes = json.loads(self.detalhes)
        total = sum(float(item['valor_total']) for item in detalhes)
        return total

    def restock_items(self):
        detalhes = json.loads(self.detalhes)
        for item in detalhes:
            produto = Produto.objects.get(nome_produto=item['nome_produto'])
            estoque_item = Estoque.objects.get(produto=produto)
            estoque_item.quantidade += int(item['quantidade'])
            estoque_item.save()

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = Vendas.objects.get(pk=self.pk)
            if old_instance.processo != 'cancelado' and self.processo == 'cancelado':
                self.restock_items()
        super(Vendas, self).save(*args, **kwargs)