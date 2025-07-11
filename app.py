from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware

# Importe o Admin e ModelView do sqladmin
from sqladmin import Admin, ModelView

import models
import schemas
from database import SessionLocal, engine
import auth_utils # Contém authenticate_funcionario, create_access_token, TokenPayload, e get_current_active_funcionario

# Importar todos os seus routers
from routers import produtos_router
from routers import funcionarios_router
from routers import clientes_router
from routers import pedidos_router
from routers import pedido_itens_router
from routers import vendas_router

# Cria as tabelas no banco de dados se elas não existirem
# NOTA: Esta função cria APENAS tabelas que não existem.
# Se você alterar a estrutura de uma tabela existente (adicionar/remover colunas),
# você precisará de uma ferramenta de migração (como Alembic) para atualizar o banco de dados.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TalkStoque API",
    version="0.4.2", # Versão atualizada para refletir as mudanças
    description="API para gerenciamento de estoque, com autenticação JWT e rotas modulares, e painel administrativo via SQLAdmin."
)

# Define as origens permitidas para CORS
origins = [
    "http://localhost:5173", # URL do seu frontend React em desenvolvimento
]

# Adiciona o middleware CORS à aplicação
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Lista de origens que podem fazer requisições
    allow_credentials=True, # Permite cookies/tokens de autorização em requisições cross-origin
    allow_methods=["*"],    # Métodos HTTP permitidos (ex: GET, POST, PUT, DELETE)
    allow_headers=["*"],    # Cabeçalhos HTTP permitidos
)

# Dependência para obter a sessão do banco de dados
def get_db_main_app():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rota de autenticação para gerar token JWT
@app.post("/token", response_model=schemas.Token, tags=["Autenticação"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_main_app)
):
    funcionario = auth_utils.authenticate_funcionario(db, email=form_data.username, password=form_data.password)
    if not funcionario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={"sub": funcionario.email, "id": funcionario.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Rota para obter informações do token atual
@app.get("/me/token-info", response_model=auth_utils.TokenPayload, tags=["Autenticação"])
async def read_my_token_info(
    current_funcionario: models.Funcionario = Depends(auth_utils.get_current_active_funcionario)
):
    return auth_utils.TokenPayload(sub=current_funcionario.email, id=current_funcionario.id)

# Inclui todos os routers da API
app.include_router(produtos_router.router)
app.include_router(funcionarios_router.router)
app.include_router(clientes_router.router)
app.include_router(pedidos_router.router)
app.include_router(pedido_itens_router.router)
app.include_router(vendas_router.router)

# ----------------------------------------------------
# Integração com SQLAdmin para o painel administrativo
# ----------------------------------------------------

# Instancia o Admin, conectando-o à aplicação FastAPI e ao engine do SQLAlchemy
admin = Admin(app, engine)

# Define as classes ModelView para cada modelo do banco de dados que você deseja gerenciar.
# Isso configura como cada modelo aparecerá e será interagir no painel admin.

class ProdutoAdmin(ModelView, model=models.Produto):
    # column_list: Define as colunas visíveis na listagem principal do admin para este modelo.
    column_list = [models.Produto.id, models.Produto.nome, models.Produto.preco, models.Produto.quantidade_estoque, models.Produto.categoria, models.Produto.data_cadastro]
    # column_details_list: Define as colunas visíveis na página de detalhes de um item individual.
    column_details_list = column_list + [models.Produto.descricao]
    # column_searchable_list: Permite pesquisar por estas colunas.
    column_searchable_list = [models.Produto.nome, models.Produto.categoria]
    # column_sortable_list: Permite ordenar a lista por estas colunas.
    column_sortable_list = [models.Produto.id, models.Produto.nome, models.Produto.preco, models.Produto.quantidade_estoque, models.Produto.data_cadastro]

class FuncionarioAdmin(ModelView, model=models.Funcionario):
    # CORRIGIDO: Removido 'models.Funcionario.ativo' pois não existe no seu esquema SQL.
    column_list = [models.Funcionario.id, models.Funcionario.nome, models.Funcionario.email, models.Funcionario.cargo, models.Funcionario.data_contratacao]
    # Evite listar a coluna de senha diretamente por segurança.
    column_searchable_list = [models.Funcionario.nome, models.Funcionario.email, models.Funcionario.cargo]
    column_sortable_list = [models.Funcionario.id, models.Funcionario.nome, models.Funcionario.email, models.Funcionario.cargo, models.Funcionario.data_contratacao]

class ClienteAdmin(ModelView, model=models.Cliente):
    column_list = [models.Cliente.id, models.Cliente.nome, models.Cliente.email, models.Cliente.telefone, models.Cliente.endereco, models.Cliente.data_cadastro]
    column_searchable_list = [models.Cliente.nome, models.Cliente.email, models.Cliente.telefone]
    column_sortable_list = [models.Cliente.id, models.Cliente.nome, models.Cliente.email, models.Cliente.data_cadastro]

class PedidoAdmin(ModelView, model=models.Pedido):
    # Ajustado para usar 'total' conforme seu esquema SQL
    column_list = [models.Pedido.id, models.Pedido.data_pedido, models.Pedido.status, models.Pedido.total, models.Pedido.cliente_id]
    # Você pode querer adicionar um campo de relacionamento para mostrar o nome do cliente em vez do ID
    column_searchable_list = [models.Pedido.status]
    column_sortable_list = [models.Pedido.id, models.Pedido.data_pedido, models.Pedido.status, models.Pedido.total]

class PedidoItemAdmin(ModelView, model=models.PedidoItem):
    column_list = [models.PedidoItem.id, models.PedidoItem.pedido_id, models.PedidoItem.produto_id, models.PedidoItem.quantidade, models.PedidoItem.preco_unitario]
    column_sortable_list = [models.PedidoItem.id, models.PedidoItem.pedido_id, models.PedidoItem.produto_id]

class VendaAdmin(ModelView, model=models.Venda):
    # Ajustado para usar 'forma_pagamento' conforme seu esquema SQL
    column_list = [models.Venda.id, models.Venda.data_venda, models.Venda.valor_total, models.Venda.forma_pagamento, models.Venda.pedido_id, models.Venda.funcionario_id]
    column_searchable_list = [models.Venda.forma_pagamento]
    column_sortable_list = [models.Venda.id, models.Venda.data_venda, models.Venda.valor_total]


# Adiciona todas as ModelViews criadas à instância do SQLAdmin.
# Isso as torna acessíveis no painel administrativo.
admin.add_view(ProdutoAdmin)
admin.add_view(FuncionarioAdmin)
admin.add_view(ClienteAdmin)
admin.add_view(PedidoAdmin)
admin.add_view(PedidoItemAdmin)
admin.add_view(VendaAdmin)

# ----------------------------------------------------
# Fim da integração com SQLAdmin
# ----------------------------------------------------

# Rota raiz da API, atualizada para mencionar o painel de administração
@app.get("/", tags=["Root"])
async def home():
    return {"message": "Bem-vindo à TalkStoque API! Acesse /docs para a documentação interativa e /admin para o painel de administração."}