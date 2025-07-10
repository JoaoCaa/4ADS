from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from typing import List
from datetime import datetime, timedelta
from decimal import Decimal

import models
import schemas
from database import SessionLocal
from auth_utils import get_current_active_funcionario

router = APIRouter(
    prefix="/vendas",
    tags=["Vendas"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Venda, status_code=status.HTTP_201_CREATED)
def create_venda(
    venda_data: schemas.VendaCreate, 
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == venda_data.pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pedido com id {venda_data.pedido_id} não encontrado.")
    if pedido.venda:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Pedido com id {venda_data.pedido_id} já possui uma venda associada.")

    if venda_data.funcionario_id:
        funcionario_db_check = db.query(models.Funcionario).filter(models.Funcionario.id == venda_data.funcionario_id).first()
        if not funcionario_db_check:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Funcionário com id {venda_data.funcionario_id} não encontrado.")

    db_venda = models.Venda(**venda_data.model_dump())
    db.add(db_venda)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro ao criar venda: {str(e)}")
    db.refresh(db_venda)
    return db_venda

@router.get("/{venda_id}", response_model=schemas.Venda)
def read_venda(
    venda_id: int, 
    db: Session = Depends(get_db), 
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_venda = db.query(models.Venda).filter(models.Venda.id == venda_id).first()
    if db_venda is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")
    return db_venda

@router.get("/estatisticas/valor-total", response_model=schemas.ValorVendido)
def get_soma_total_vendido(
    apenas_ultimo_mes: bool = False, # Parâmetro de consulta: /estatisticas/valor-total?apenas_ultimo_mes=true
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    """
    Calcula a soma total do valor das vendas.
    Se 'apenas_ultimo_mes' for True, calcula a soma apenas para o último mês calendário completo.
    Por exemplo, se a data atual for em Junho, considerará as vendas de 1 de Maio a 31 de Maio.
    """
    # Inicia a query para somar a coluna 'valor_total' do modelo 'Venda'
    # sql_func.sum retorna um valor que pode ser None se não houver linhas para somar
    query_sum = db.query(sql_func.sum(models.Venda.valor_total).label("total_valor_vendido"))

    if apenas_ultimo_mes:
        hoje = datetime.utcnow() # Use datetime.now() se seu banco de dados e aplicação não usam UTC consistentemente

        # Calcula o primeiro dia do mês atual (ex: se hoje é 15/06/2024, será 01/06/2024 00:00:00)
        primeiro_dia_mes_atual = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # O último dia do mês passado é o primeiro dia do mês atual menos um dia
        # (ex: 01/06/2024 - 1 dia = 31/05/2024)
        ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)
        
        # O primeiro dia do mês passado é o último dia do mês passado com o dia ajustado para 1
        # (ex: 31/05/2024 -> 01/05/2024 00:00:00)
        primeiro_dia_mes_passado = ultimo_dia_mes_passado.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Adiciona o filtro à query:
        # Vendas com data_venda >= primeiro_dia_mes_passado E data_venda < primeiro_dia_mes_atual
        # Isso cobre todo o mês passado. (ex: [01/05/2024 00:00:00, 01/06/2024 00:00:00) )
        query_sum = query_sum.filter(
            models.Venda.data_venda >= primeiro_dia_mes_passado,
            models.Venda.data_venda < primeiro_dia_mes_atual
        )
    
    # Executa a query e obtém o resultado. .scalar() retorna o primeiro valor da primeira linha, ou None.
    total_calculado = query_sum.scalar()
    
    # Se não houver vendas no período (ou nenhuma venda no total), total_calculado será None.
    # Nesse caso, retornamos Decimal('0.00').
    valor_final = total_calculado if total_calculado is not None else Decimal("0.00")
    
    # O FastAPI validará este dicionário contra o response_model schemas.ValorVendido
    return {"total": valor_final}

@router.get("/", response_model=List[schemas.Venda])
def read_vendas(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    vendas = db.query(models.Venda).offset(skip).limit(limit).all()
    return vendas

@router.put("/{venda_id}", response_model=schemas.Venda)
def update_venda(
    venda_id: int, 
    venda_update: schemas.VendaUpdate, 
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_venda = db.query(models.Venda).filter(models.Venda.id == venda_id).first()
    if db_venda is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")

    update_data = venda_update.model_dump(exclude_unset=True)
    if "funcionario_id" in update_data and update_data["funcionario_id"] is not None:
        funcionario_check = db.query(models.Funcionario).filter(models.Funcionario.id == update_data["funcionario_id"]).first()
        if not funcionario_check:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Funcionário com id {update_data['funcionario_id']} não encontrado.")

    for key, value in update_data.items():
        setattr(db_venda, key, value)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro ao atualizar venda: {str(e)}")
    db.refresh(db_venda)
    return db_venda

@router.delete("/{venda_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_venda(
    venda_id: int, 
    db: Session = Depends(get_db),
    current_funcionario: models.Funcionario = Depends(get_current_active_funcionario)
):
    db_venda = db.query(models.Venda).filter(models.Venda.id == venda_id).first()
    if db_venda is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")
    db.delete(db_venda)
    db.commit()
    return