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
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    # Datos del cliente
    cliente = db.Column(db.String(100), nullable=False)
    cliente_telefono = db.Column(db.String(30))
    cliente_email = db.Column(db.String(120))
    # Datos del dispositivo (compatibilidad + normalizado)
    dispositivo = db.Column(db.String(200), nullable=False)  # Texto libre para mantener compatibilidad
    device_type = db.Column(db.String(50))
    device_brand = db.Column(db.String(50))
    device_model = db.Column(db.String(100))
    # Información técnica
    falla = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.Text)
    required_parts = db.Column(db.Text)
    repair_cost = db.Column(db.String(50))
    estado = db.Column(db.String(50), default="RECIBIDO")
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, onupdate=datetime.utcnow)
