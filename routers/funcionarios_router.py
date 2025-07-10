from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

import models
import schemas
from database import SessionLocal
import auth_utils
from auth_utils import get_password_hash, get_current_active_funcionario # Importa a dependência

router = APIRouter(
    prefix="/funcionarios",
    tags=["Funcionários"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Funcionario, status_code=status.HTTP_201_CREATED) # PÚBLICO
def create_funcionario(funcionario: schemas.FuncionarioCreate, db: Session = Depends(get_db)):
    db_funcionario_check = db.query(models.Funcionario).filter(models.Funcionario.email == funcionario.email).first()
    if db_funcionario_check:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já registrado")

    hashed_password = get_password_hash(funcionario.senha)
    db_funcionario = models.Funcionario(
        nome=funcionario.nome,
        email=funcionario.email,
        cargo=funcionario.cargo,
        senha=hashed_password
    )
    db.add(db_funcionario)
    db.commit()
    db.refresh(db_funcionario)
    return db_funcionario

@router.get("/me", response_model=schemas.Funcionario)
async def read_funcionarios_me(current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)):
    return current_funcionario

@router.get("/total", response_model=schemas.TotalFuncionarios)
def get_total_funcionarios(
    db: Session = Depends(get_db),
    current_funcionario_auth: models.Funcionario = Depends(auth_utils.get_current_active_funcionario) # Protegendo o endpoint
):
    """
    Retorna a contagem total de funcionários cadastrados.
    """
    # func.count(models.Funcionario.id) faz a contagem dos IDs dos funcionários
    # .scalar() retorna o valor da contagem diretamente
    total_count = db.query(func.count(models.Funcionario.id)).scalar()
    
    return {"total_funcionarios": total_count if total_count is not None else 0}

@router.get("/{funcionario_id}", response_model=schemas.Funcionario)
def read_funcionario(
    funcionario_id: int, 
    db: Session = Depends(get_db),
    current_user_auth: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_funcionario_local = db.query(models.Funcionario).filter(models.Funcionario.id == funcionario_id).first()
    if db_funcionario_local is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado")
    # Adicionar lógica de permissão se necessário (ex: admin ou próprio usuário)
    return db_funcionario_local

@router.get("/", response_model=List[schemas.Funcionario])
def read_funcionarios(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    funcionarios = db.query(models.Funcionario).offset(skip).limit(limit).all()
    return funcionarios

@router.put("/{funcionario_id}", response_model=schemas.Funcionario)
def update_funcionario(
    funcionario_id: int, 
    funcionario_update: schemas.FuncionarioUpdate, 
    db: Session = Depends(get_db),
    current_user: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_funcionario = db.query(models.Funcionario).filter(models.Funcionario.id == funcionario_id).first()
    if db_funcionario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado")
    
    # Adicionar lógica de permissão (ex: admin ou próprio usuário)
    # if current_user.id != funcionario_id and not getattr(current_user, 'is_admin', False):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Não autorizado")

    update_data = funcionario_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_funcionario, key, value)
    
    db.commit()
    db.refresh(db_funcionario)
    return db_funcionario

@router.delete("/{funcionario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_funcionario(
    funcionario_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_funcionario = db.query(models.Funcionario).filter(models.Funcionario.id == funcionario_id).first()
    if db_funcionario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado")
    
    # Adicionar lógica de permissão
    # if current_user.id != funcionario_id and not getattr(current_user, 'is_admin', False):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Não autorizado")

    db.delete(db_funcionario)
    db.commit()
    return