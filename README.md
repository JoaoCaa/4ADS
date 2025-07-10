# TalkStoque - Backend

Este é o backend do sistema **TalkStoque**, desenvolvido em **Python** com **FastAPI**, responsável por fornecer a API REST para o gerenciamento de estoque, pedidos, vendas, clientes e funcionários de um armazém de bebidas.

---

## 🧠 Tecnologias Utilizadas

- Python 3.11+
- FastAPI
- SQLAlchemy
- MySQL (via XAMPP)
- PyMySQL
- JWT (python-jose)
- Uvicorn

---

## ⚙️ Pré-requisitos

1. **Python 3.11+** instalado
2. **XAMPP** com MySQL e Apache em execução
3. Banco de dados MySQL criado com o nome e estrutura compatíveis conforme código presente no arquivo de texto db.txt

---

## 🛠️ Criação do Banco de Dados

Abra o painel do XAMPP e inicie o serviço **MySQL**. Em seguida, acesse o **phpMyAdmin** ou use um cliente MySQL e execute os comandos para criar o banco de dados.

---

## 📦 Instalação

1. Clone o repositório:

```bash
git clone https://github.com/DiogoSion/TalkStoque_API/tree/main
cd talkstoque-backend
```

2. Crie um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## 🚀 Executando o Projeto

```bash
uvicorn main:app --reload
```

A API estará disponível em:

```
http://127.0.0.1:8000
```

A documentação automática estará em:

- Swagger: http://127.0.0.1:8000/docs
- Redoc: http://127.0.0.1:8000/redoc

---

## 🔗 Frontend

O frontend do sistema TalkStoque está disponível aqui:  
[Link para o Frontend - TalkStoque](https://github.com/DiogoSion/TalkStoque)

---

## 📌 Observações

- Certifique-se de que o banco MySQL e o APACHE Tomcat esteja ativo no XAMPP.
- O projeto utiliza autenticação com JWT para proteger rotas.

---
