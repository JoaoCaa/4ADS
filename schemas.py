from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# --- Schemas de Autenticação ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    funcionario_id: Optional[int] = None

# Schemas para Produto
class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: Decimal
    quantidade_estoque: int
    categoria: Optional[str] = None

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(ProdutoBase):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[Decimal] = None
    quantidade_estoque: Optional[int] = None
    categoria: Optional[str] = None

class TotalEstoque(BaseModel):
    total_itens_estoque: int

class Produto(ProdutoBase):
    id: int
    data_cadastro: datetime

    class Config:
        from_attributes = True


# Schemas para Funcionario
class FuncionarioBase(BaseModel):
    nome: str
    email: str # Usado como username
    cargo: Optional[str] = None

class FuncionarioCreate(FuncionarioBase):
    senha: str # Senha é obrigatória na criação

class FuncionarioUpdate(FuncionarioBase): # Não permitir atualização de senha por aqui
    nome: Optional[str] = None
    email: Optional[str] = None # Considere se a atualização de email deve ser permitida e como afeta o login
    cargo: Optional[str] = None

class TotalFuncionarios(BaseModel):
    total_funcionarios: int

class Funcionario(FuncionarioBase):
    id: int
    data_contratacao: datetime
    # Não retorne a senha

    class Config:
        from_attributes = True


# Schemas para Cliente
class ClienteBase(BaseModel):
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(ClienteBase):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None


class Cliente(ClienteBase):
    id: int
    data_cadastro: datetime
    # pedidos: List['Pedido'] = [] # Definido abaixo

    class Config:
        from_attributes = True


# Schemas para PedidoItem
class PedidoItemBase(BaseModel):
    produto_id: int
    quantidade: int
    preco_unitario: Decimal

class PedidoItemCreate(PedidoItemBase):
    pass

class PedidoItemUpdate(PedidoItemBase):
    produto_id: Optional[int] = None
    quantidade: Optional[int] = None
    preco_unitario: Optional[Decimal] = None

class PedidoItem(PedidoItemBase):
    id: int
    pedido_id: int
    # produto: Produto
    nome_produto: Optional[str] = None

    class Config:
        from_attributes = True


# Schemas para Venda
class VendaBase(BaseModel):
    funcionario_id: Optional[int] = None
    valor_total: Decimal
    forma_pagamento: Optional[str] = None

class VendaCreate(VendaBase):
    pedido_id: int

class VendaUpdate(VendaBase):
    funcionario_id: Optional[int] = None
    valor_total: Optional[Decimal] = None
    forma_pagamento: Optional[str] = None

class ValorVendido(BaseModel):
    total: Decimal

class Venda(VendaBase):
    id: int
    pedido_id: int
    data_venda: datetime
    # funcionario: Optional[Funcionario]

    class Config:
        from_attributes = True


# Schemas para Pedido
class PedidoBase(BaseModel):
    cliente_id: int
    status: Optional[str] = 'Pendente'
    total: Decimal

class PedidoCreate(PedidoBase):
    itens: List[PedidoItemCreate] = []

class PedidoUpdate(PedidoBase):
    cliente_id: Optional[int] = None
    status: Optional[str] = None
    total: Optional[Decimal] = None

class PedidoCount(BaseModel):
    total_ativos: int

class Pedido(PedidoBase):
    id: int
    data_pedido: datetime
    cliente: Cliente # Aninhado
    itens: List[PedidoItem] = [] # Aninhado
    venda: Optional[Venda] = None # Aninhado

    class Config:
        from_attributes = True

# Atualiza as referências de tipo (forward references) se necessário.
# No Pydantic V2, isso é muitas vezes automático com as anotações de string.
# Cliente.model_rebuild()
# Pedido.model_rebuild()
# etc