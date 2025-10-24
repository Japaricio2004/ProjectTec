from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # "tecnico" o "cliente"

class Orden(db.Model):
    __tablename__ = "ordenes"
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    cliente = db.Column(db.String(100), nullable=False)
    dispositivo = db.Column(db.String(100), nullable=False)
    falla = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(50), default="RECIBIDO")
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
