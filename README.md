# Sistema de Agendamento de Clientes

## Sobre o projeto

O Sistema de Agendamento de Clientes é uma API desenvolvida em Python utilizando Flask. Seu objetivo é facilitar o cadastro de clientes e o gerenciamento de agendamentos.

## Tecnologias utilizadas

- Python
- Flask
- SQLite
- Flask-SQLAlchemy
- JWT (autenticação)

## Funcionalidades

- Cadastro e login de usuários.
- Autenticação por token JWT.
- Cadastro de clientes.
- Listagem e consulta de clientes.
- Exclusão de clientes.
- Cadastro de agendamentos.
- Listagem de agendamentos.
- Verificação de horários disponíveis.
- Cancelamento de agendamentos.

## Como executar o projeto

1. Clone o repositório:

   ```bash
   git clone https://github.com/Fox0dark/Sistema-de-Agendamentos.git
   ```

2. Entre na pasta:

   ```bash
   cd Sistema-de-Agendamentos
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Execute o projeto:

   ```bash
   python app.py
   ```

5. A API estará disponível em:

   `http://127.0.0.1:5000`

## Banco de dados

O projeto utiliza SQLite para armazenar os dados de usuários, clientes e agendamentos.

## Autor

Mikael Cenedese Arévalo

Projeto desenvolvido para a disciplina de Linguagem de Programação.
