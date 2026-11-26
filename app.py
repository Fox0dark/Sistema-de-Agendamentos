
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

# CONFIGURACAO DO BANCO DE DADOS
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///agendamentos.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "chave-secreta-agendamento-2026"

db = SQLAlchemy(app)


# MODELO DE USUARIO
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)


# MODELO DE CLIENTE
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))


# MODELO DE AGENDAMENTO
class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False)
    descricao = db.Column(db.String(200))
    status = db.Column(db.String(30), default="Agendado")

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("cliente.id"),
        nullable=False
    )


# CRIAR TABELAS
with app.app_context():
    db.create_all()


# REGISTRAR USUARIO
@app.route("/usuarios/registro", methods=["POST"])
def registrar_usuario():
    dados = request.get_json(silent=True) or {}

    if not dados.get("nome") or not dados.get("email") or not dados.get("senha"):
        return jsonify({"erro": "Preencha todos os campos"}), 400

    usuario_existente = Usuario.query.filter_by(
        email=dados["email"]
    ).first()

    if usuario_existente:
        return jsonify({"erro": "Email ja cadastrado"}), 409

    usuario = Usuario(
        nome=dados["nome"],
        email=dados["email"],
        senha=generate_password_hash(dados["senha"])
    )

    db.session.add(usuario)
    db.session.commit()

    return jsonify({"mensagem": "Usuario cadastrado!"}), 201


# LOGIN
@app.route("/usuarios/login", methods=["POST"])
def login():
    dados = request.get_json(silent=True) or {}

    if not dados.get("email") or not dados.get("senha"):
        return jsonify({"erro": "Informe email e senha"}), 400

    usuario = Usuario.query.filter_by(
        email=dados["email"]
    ).first()

    if not usuario or not check_password_hash(
        usuario.senha, str(dados["senha"])
    ):
        return jsonify({"erro": "Email ou senha incorretos"}), 401

    token = jwt.encode(
        {
            "usuario_id": usuario.id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=2)
        },
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    return jsonify({
        "mensagem": "Login realizado!",
        "token": token
    }), 200


# VALIDAR TOKEN
def token_obrigatorio(funcao):
    @wraps(funcao)
    def decorada(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token or not token.startswith("Bearer "):
            return jsonify({"erro": "Token nao informado"}), 401

        try:
            token = token.replace("Bearer ", "", 1)

            dados = jwt.decode(
                token,
                app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )

            usuario = db.session.get(
                Usuario, dados["usuario_id"]
            )

            if not usuario:
                return jsonify({"erro": "Usuario nao encontrado"}), 401

        except (JWTError, KeyError):
            return jsonify({"erro": "Token invalido ou expirado"}), 401

        return funcao(*args, **kwargs)

    return decorada


# ROTA INICIAL
@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "mensagem": "Sistema de Agendamento funcionando!",
        "banco": "SQLite conectado"
    })


# CADASTRAR CLIENTE
@app.route("/clientes", methods=["POST"])
@token_obrigatorio
def cadastrar_cliente():
    dados = request.get_json(silent=True) or {}

    if not dados.get("nome") or not dados.get("telefone"):
        return jsonify({
            "erro": "Nome e telefone sao obrigatorios"
        }), 400

    cliente = Cliente(
        nome=dados["nome"],
        telefone=dados["telefone"],
        email=dados.get("email")
    )

    db.session.add(cliente)
    db.session.commit()

    return jsonify({
        "mensagem": "Cliente cadastrado!",
        "id": cliente.id
    }), 201


# LISTAR CLIENTES
@app.route("/clientes", methods=["GET"])
@token_obrigatorio
def listar_clientes():
    clientes = Cliente.query.all()

    return jsonify([
        {
            "id": c.id,
            "nome": c.nome,
            "telefone": c.telefone,
            "email": c.email
        }
        for c in clientes
    ])


# VISUALIZAR CLIENTE
@app.route("/clientes/<int:id>", methods=["GET"])
@token_obrigatorio
def visualizar_cliente(id):
    cliente = db.session.get(Cliente, id)

    if not cliente:
        return jsonify({"erro": "Cliente nao encontrado"}), 404

    return jsonify({
        "id": cliente.id,
        "nome": cliente.nome,
        "telefone": cliente.telefone,
        "email": cliente.email
    })


# EXCLUIR CLIENTE
@app.route("/clientes/<int:id>", methods=["DELETE"])
@token_obrigatorio
def excluir_cliente(id):
    cliente = db.session.get(Cliente, id)

    if not cliente:
        return jsonify({"erro": "Cliente nao encontrado"}), 404

    # EVITA EXCLUIR CLIENTE QUE POSSUI AGENDAMENTOS
    if Agendamento.query.filter_by(cliente_id=id).first():
        return jsonify({
            "erro": "Cliente possui agendamentos e nao pode ser excluido"
        }), 409

    db.session.delete(cliente)
    db.session.commit()

    return jsonify({"mensagem": "Cliente excluido!"})


# CADASTRAR AGENDAMENTO
@app.route("/agendamentos", methods=["POST"])
@token_obrigatorio
def cadastrar_agendamento():
    dados = request.get_json(silent=True) or {}

    if not dados.get("data_hora") or not dados.get("cliente_id"):
        return jsonify({
            "erro": "Informe data_hora e cliente_id"
        }), 400

    cliente = db.session.get(Cliente, dados["cliente_id"])

    if not cliente:
        return jsonify({"erro": "Cliente nao encontrado"}), 404

    try:
        data_hora = datetime.fromisoformat(dados["data_hora"])
    except (ValueError, TypeError):
        return jsonify({
            "erro": "Data invalida. Use AAAA-MM-DDTHH:MM:SS"
        }), 400

    conflito = Agendamento.query.filter_by(
        data_hora=data_hora,
        status="Agendado"
    ).first()

    if conflito:
        return jsonify({"erro": "Horario ja ocupado"}), 409

    agendamento = Agendamento(
        data_hora=data_hora,
        descricao=dados.get("descricao", ""),
        cliente_id=cliente.id
    )

    db.session.add(agendamento)
    db.session.commit()

    return jsonify({
        "mensagem": "Agendamento criado!",
        "id": agendamento.id
    }), 201


# LISTAR AGENDAMENTOS
@app.route("/agendamentos", methods=["GET"])
@token_obrigatorio
def listar_agendamentos():
    agendamentos = Agendamento.query.all()

    return jsonify([
        {
            "id": a.id,
            "data_hora": a.data_hora.isoformat(),
            "descricao": a.descricao,
            "status": a.status,
            "cliente_id": a.cliente_id
        }
        for a in agendamentos
    ])


# CANCELAR AGENDAMENTO
@app.route("/agendamentos/<int:id>", methods=["DELETE"])
@token_obrigatorio
def cancelar_agendamento(id):
    agendamento = db.session.get(Agendamento, id)

    if not agendamento:
        return jsonify({
            "erro": "Agendamento nao encontrado"
        }), 404

    agendamento.status = "Cancelado"
    db.session.commit()

    return jsonify({"mensagem": "Agendamento cancelado!"})


# EXECUTAR A API
if __name__ == "__main__":
    print("\nROTAS DISPONIVEIS:")
    print(app.url_map)
    app.run(debug=True)
