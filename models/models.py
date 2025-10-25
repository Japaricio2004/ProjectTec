from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo

db = SQLAlchemy()

# Zona horaria de Perú
PERU_TZ = ZoneInfo("America/Lima")

def get_peru_time():
    """Retorna la hora actual en zona horaria de Perú (sin timezone info para SQLite)"""
    return datetime.now(PERU_TZ).replace(tzinfo=None)

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

    # Técnico asignado
    tecnico_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    tecnico = db.relationship('Usuario', foreign_keys=[tecnico_id])

    # Datos del dispositivo (compatibilidad + normalizado)
    dispositivo = db.Column(db.String(200), nullable=False)  
    device_type = db.Column(db.String(50))
    device_brand = db.Column(db.String(50))
    device_model = db.Column(db.String(100))
    # Información técnica
    falla = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.Text)
    required_parts = db.Column(db.Text)
    repair_cost = db.Column(db.String(50))
    estado = db.Column(db.String(50), default="RECIBIDO")
    fecha_creacion = db.Column(db.DateTime, default=get_peru_time)
    fecha_actualizacion = db.Column(db.DateTime, onupdate=get_peru_time)

class Valoracion(db.Model):
    __tablename__ = "valoraciones"
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes.id'), unique=True, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 a 5
    comentario = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=get_peru_time)

    orden = db.relationship('Orden', backref=db.backref('valoracion', uselist=False))
