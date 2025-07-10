from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import SessionLocal
from auth_utils import get_current_active_funcionario

router = APIRouter(
    prefix="/pedido_itens",
    tags=["Itens de Pedido"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# POST geralmente seria parte da criação do Pedido, mas se precisar de um endpoint individual:
@router.post("/", response_model=schemas.PedidoItem, status_code=status.HTTP_201_CREATED)
def create_pedido_item(
    item: schemas.PedidoItemCreate, 
    pedido_id: int = Query(..., description="ID do Pedido ao qual este item pertence"), 
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pedido com id {pedido_id} não encontrado.")
    
    produto = db.query(models.Produto).filter(models.Produto.id == item.produto_id).first()
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Produto com id {item.produto_id} não encontrado.")
    
    # Adicionar lógica de estoque aqui também se itens são adicionados individualmente
    if produto.quantidade_estoque < item.quantidade:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estoque insuficiente para {produto.nome}.")
    produto.quantidade_estoque -= item.quantidade
    db.add(produto)

    db_item = models.PedidoItem(**item.model_dump(), pedido_id=pedido_id)
    db.add(db_item)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro ao criar item de pedido: {str(e)}")
    db.refresh(db_item)
    return db_item

@router.get("/{item_id}", response_model=schemas.PedidoItem)
def read_pedido_item(
    item_id: int, 
    db: Session = Depends(get_db), 
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_item = db.query(models.PedidoItem).filter(models.PedidoItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de pedido não encontrado")
    return db_item

# Rota para listar itens de um pedido específico (já estava no app.py, pode ser movida ou duplicada aqui com prefixo diferente)
# Se movida para cá, o prefixo /pedido_itens não se encaixa bem.
# Melhor manter em pedidos_router.py ou criar uma rota específica aqui como:
# @router.get("/por_pedido/{pedido_id}", response_model=List[schemas.PedidoItem]) ...

@router.put("/{item_id}", response_model=schemas.PedidoItem)
def update_pedido_item(
    item_id: int, 
    item_update: schemas.PedidoItemUpdate, 
    db: Session = Depends(get_db), 
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_item = db.query(models.PedidoItem).filter(models.PedidoItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de pedido não encontrado")

    update_data = item_update.model_dump(exclude_unset=True)
    
    # Lógica de ajuste de estoque se quantidade ou produto mudar
    # (complexo, pois precisa do estado antigo e novo)

    if "produto_id" in update_data:
        produto = db.query(models.Produto).filter(models.Produto.id == update_data["produto_id"]).first()
        if not produto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Produto com id {update_data['produto_id']} não encontrado.")
    
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro ao atualizar item: {str(e)}")
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pedido_item(
    item_id: int, 
    db: Session = Depends(get_db), 
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_item = db.query(models.PedidoItem).filter(models.PedidoItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de pedido não encontrado")
    
    # Lógica para reverter estoque e total do pedido
    produto = db.query(models.Produto).filter(models.Produto.id == db_item.produto_id).first()
    if produto:
        produto.quantidade_estoque += db_item.quantidade
        db.add(produto)
        
    db.delete(db_item)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro ao deletar item: {str(e)}")
    return