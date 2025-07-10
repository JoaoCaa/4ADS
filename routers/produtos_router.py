from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional

import models
import schemas
from database import SessionLocal
from auth_utils import get_current_active_funcionario

router = APIRouter(
    prefix="/produtos",
    tags=["Produtos"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Produto, status_code=status.HTTP_201_CREATED)
def create_produto(
    produto: schemas.ProdutoCreate,
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_produto = models.Produto(**produto.model_dump())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@router.get("/{produto_id}", response_model=schemas.Produto)
def read_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if db_produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return db_produto

@router.get("/", response_model=List[schemas.Produto])
def read_produtos(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    query = db.query(models.Produto)

    if search:
        search_term = f"%{search.lower()}%" # Converte o termo de busca para minúsculas para busca case-insensitive
        query = query.filter(
            or_(
                func.lower(models.Produto.nome).like(search_term),
                func.lower(models.Produto.descricao).like(search_term),
                func.lower(models.Produto.categoria).like(search_term)
            )
        )
    
    produtos = query.offset(skip).limit(limit).all()
    return produtos

@router.put("/{produto_id}", response_model=schemas.Produto)
def update_produto(
    produto_id: int,
    produto_update: schemas.ProdutoUpdate,
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if db_produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    
    update_data = produto_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_produto, key, value)
    
    db.commit()
    db.refresh(db_produto)
    return db_produto

@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if db_produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    db.delete(db_produto)
    db.commit()
    return

@router.get("/estoque/total", response_model=schemas.TotalEstoque)
def get_total_estoque(
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario) # Protegendo o endpoint
):
    """
    Retorna a soma total da quantidade de todos os produtos em estoque.
    """
    # func.sum(models.Produto.quantidade_estoque) faz a soma da coluna quantidade_estoque
    # .scalar() retorna o valor da soma diretamente
    total_stock = db.query(func.sum(models.Produto.quantidade_estoque)).scalar()
    
    return {"total_itens_estoque": total_stock if total_stock is not None else 0}