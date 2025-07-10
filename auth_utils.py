from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel # Se TokenData estiver aqui, caso contrário, importe de schemas
from sqlalchemy.orm import Session

import models # Seus modelos SQLAlchemy
from database import SessionLocal # Para a dependência get_db dentro de get_current_funcionario

# Configurações de Segurança
SECRET_KEY = "c5e478d3f5b7a8e8b3f5843a7d3e1e8b4f17c5f8be07f21d8d7a4ec4ff7074c8"  # Troque por uma chave forte e aleatória!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto para Hashing de Senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # O endpoint /token estará no app.py principal

# Schema para dados do token (pode ficar aqui ou em schemas.py)
class TokenDataPayload(BaseModel):
    email: Optional[str] = None
    funcionario_id: Optional[int] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None 
    id: Optional[int] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Função auxiliar para obter a sessão do banco de dados (pode ser usada internamente aqui)
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_funcionario(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db_session) # Usa o get_db_session local
) -> models.Funcionario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        funcionario_id: Optional[int] = payload.get("id") # Certifique-se que 'id' está no payload do token
        if email is None or funcionario_id is None:
            raise credentials_exception
        token_data = TokenDataPayload(email=email, funcionario_id=funcionario_id)
    except JWTError:
        raise credentials_exception
    
    funcionario = db.query(models.Funcionario).filter(models.Funcionario.id == token_data.funcionario_id).first()
    # ou: funcionario = db.query(models.Funcionario).filter(models.Funcionario.email == token_data.email).first()

    if funcionario is None:
        raise credentials_exception
    return funcionario

async def get_current_active_funcionario(
    current_funcionario: models.Funcionario = Depends(get_current_funcionario)
) -> models.Funcionario:
    # if not current_funcionario.is_active: # Exemplo de verificação de status
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Funcionário inativo")
    return current_funcionario

# Função de autenticação (usada pelo endpoint /token no app.py)
def authenticate_funcionario(db: Session, email: str, password: str) -> Optional[models.Funcionario]:
    funcionario = db.query(models.Funcionario).filter(models.Funcionario.email == email).first()
    if not funcionario:
        return None
    if not verify_password(password, funcionario.senha):
        return None
    return funcionario