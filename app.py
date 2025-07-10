from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware

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

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TalkStoque API",
    version="0.4.1",
    description="API para gerenciamento de estoque, com autenticação JWT e rotas modulares."
)

#    Define as origens permitidas para CORS
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


def get_db_main_app():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

@app.get("/me/token-info", response_model=auth_utils.TokenPayload, tags=["Autenticação"])
async def read_my_token_info(
    current_funcionario: models.Funcionario = Depends(auth_utils.get_current_active_funcionario)
):
    return auth_utils.TokenPayload(sub=current_funcionario.email, id=current_funcionario.id)


app.include_router(produtos_router.router)
app.include_router(funcionarios_router.router)
app.include_router(clientes_router.router)
app.include_router(pedidos_router.router)
app.include_router(pedido_itens_router.router)
app.include_router(vendas_router.router)


@app.get("/", tags=["Root"])
async def home():
    return {"message": "Bem-vindo à TalkStoque API! Acesse /docs para a documentação interativa."}