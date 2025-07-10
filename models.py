from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

# Importa a classe Base do seu arquivo database.py
from database import Base


class Produto(Base):
    __tablename__ = "Produto"  # Nome da tabela no banco de dados

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    preco = Column(Numeric(10, 2), nullable=False)
    quantidade_estoque = Column(Integer, nullable=False)
    categoria = Column(String(100), nullable=True)
    data_cadastro = Column(DateTime, server_default=func.now())

    # Relacionamento: Um produto pode estar em muitos itens de pedido
    pedido_itens = relationship("PedidoItem", back_populates="produto")


class Funcionario(Base):
    __tablename__ = "Funcionario"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    senha = Column(String(255), nullable=False)  # Lembre-se de tratar o hashing da senha na aplicação
    cargo = Column(String(100), nullable=True)
    data_contratacao = Column(DateTime, server_default=func.now())

    # Relacionamento: Um funcionário pode estar associado a muitas vendas
    vendas = relationship("Venda", back_populates="funcionario")


class Cliente(Base):
    __tablename__ = "Cliente"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    telefone = Column(String(20), nullable=True)
    endereco = Column(Text, nullable=True)
    data_cadastro = Column(DateTime, server_default=func.now())

    # Relacionamento: Um cliente pode ter muitos pedidos
    # O cascade="all, delete" garante que os pedidos do cliente sejam deletados se o cliente for deletado (nível ORM)
    pedidos = relationship("Pedido", back_populates="cliente", cascade="all, delete")


class Pedido(Base):
    __tablename__ = "Pedido"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # ForeignKey com ondelete="CASCADE" reflete o comportamento do SQL
    cliente_id = Column(Integer, ForeignKey("Cliente.id", ondelete="CASCADE"), nullable=False)
    data_pedido = Column(DateTime, server_default=func.now())
    status = Column(String(50), server_default='Pendente') # server_default para default a nível de DB
    total = Column(Numeric(10, 2), nullable=False)

    # Relacionamento: Um pedido pertence a um cliente
    cliente = relationship("Cliente", back_populates="pedidos")
    # Relacionamento: Um pedido pode ter muitos itens
    # cascade="all, delete-orphan" garante que itens sejam deletados se o pedido for deletado ou se um item for removido da coleção
    itens = relationship("PedidoItem", back_populates="pedido", cascade="all, delete-orphan")
    # Relacionamento: Um pedido pode ter uma venda associada (assumindo 1 para 1)
    venda = relationship("Venda", back_populates="pedido", uselist=False, cascade="all, delete-orphan")


class PedidoItem(Base):
    __tablename__ = "PedidoItem"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("Pedido.id", ondelete="CASCADE"), nullable=False)
    produto_id = Column(Integer, ForeignKey("Produto.id", ondelete="CASCADE"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)

    # Relacionamento: Um item de pedido pertence a um pedido
    pedido = relationship("Pedido", back_populates="itens")
    # Relacionamento: Um item de pedido refere-se a um produto
    produto = relationship("Produto", back_populates="pedido_itens")

    # Propriedade híbrida para acessar o nome do produto diretamente
    @hybrid_property
    def nome_produto(self):
        if self.produto:
            return self.produto.nome
        return None


class Venda(Base):
    __tablename__ = "Venda"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # unique=True aqui, assumindo que um pedido só pode gerar uma venda.
    pedido_id = Column(Integer, ForeignKey("Pedido.id", ondelete="CASCADE"), nullable=False, unique=True)
    # ondelete="SET NULL" para funcionario_id
    funcionario_id = Column(Integer, ForeignKey("Funcionario.id", ondelete="SET NULL"), nullable=True)
    data_venda = Column(DateTime, server_default=func.now())
    valor_total = Column(Numeric(10, 2), nullable=False)
    forma_pagamento = Column(String(50), nullable=True)

    # Relacionamento: A venda está associada a um pedido
    pedido = relationship("Pedido", back_populates="venda")
    # Relacionamento: A venda pode estar associada a um funcionário
    funcionario = relationship("Funcionario", back_populates="vendas")