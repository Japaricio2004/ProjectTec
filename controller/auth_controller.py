from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models.models import db, Usuario, Orden, Valoracion
from sqlalchemy import func
from datetime import datetime

def index():
    if "usuario_id" in session:
        if session["rol"] == "tecnico":
            return redirect(url_for("technician.technician_dashboard"))
        else:
            return redirect(url_for("client_interface"))

    # Estadísticas dinámicas para la portada
    total_orders = db.session.query(Orden).count()
    delivered_orders = db.session.query(Orden).filter(Orden.estado == 'ENTREGADO').count()

    # Calcular promedio de tiempo (horas) entre creación y última actualización de órdenes entregadas
    delivered_times = db.session.query(Orden.fecha_creacion, Orden.fecha_actualizacion).filter(
        Orden.estado == 'ENTREGADO',
        Orden.fecha_creacion.isnot(None),
        Orden.fecha_actualizacion.isnot(None)
    ).all()

    total_hours = 0.0
    count_hours = 0
    for fc, fa in delivered_times:
        try:
            delta = (fa - fc).total_seconds() / 3600.0
            if delta >= 0:
                total_hours += delta
                count_hours += 1
        except Exception:
            continue

    avg_hours = (total_hours / count_hours) if count_hours > 0 else None

    # Satisfacción real: promedio de calificaciones (1-5) => porcentaje
    avg_rating = db.session.query(func.avg(Valoracion.rating)).scalar()
    if avg_rating is not None:
        satisfaction_pct = int(round((float(avg_rating) / 5.0) * 100))
    else:
        # Fallback (si aún no hay valoraciones): porcentaje entregadas / total
        satisfaction_pct = round((delivered_orders / total_orders) * 100) if total_orders > 0 else 100

    # Utilidades de formateo
    def humanize_count(n: int) -> str:
        if n is None:
            return "0"
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M+".replace('.0', '')
        if n >= 1_000:
            return f"{n/1_000:.1f}k+".replace('.0', '')
        return str(n)

    def humanize_hours(h) -> str:
        if h is None:
            return "—"
        if h < 24:
            return f"{round(h)}h"
        days = h / 24.0
        if days < 7:
            return f"{days:.1f}d".replace('.0', '')
        weeks = days / 7.0
        return f"{weeks:.1f}sem".replace('.0', '')

    stats = {
        "repairs": total_orders,
        "repairs_display": humanize_count(total_orders),
        "satisfaction": satisfaction_pct,
        "satisfaction_display": f"{satisfaction_pct}%",
        "avg_hours": avg_hours,
        "avg_time_display": humanize_hours(avg_hours),
        "delivered": delivered_orders,
    }

    # Solicitud del cliente: mostrar tiempo promedio fijo de 24h
    stats["avg_time_display"] = "24h"

    return render_template("index.html", stats=stats)

def register():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        password = request.form.get("password")
        rol = request.form.get("rol")

        if not all([nombre, correo, password, rol]):
            return render_template("register.html", error="Todos los campos son obligatorios")

        if Usuario.query.filter_by(correo=correo).first():
            return render_template("register.html", error="El correo ya está registrado")

        hashed = generate_password_hash(password)
        nuevo_usuario = Usuario(nombre=nombre, correo=correo, password=hashed, rol=rol)
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash("✅ Registro exitoso. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html")

def login():
    if request.method == "POST":
        correo = request.form.get("correo")
        password = request.form.get("password")

        usuario = Usuario.query.filter_by(correo=correo).first()
        if usuario and check_password_hash(usuario.password, password):
            session["usuario_id"] = usuario.id
            session["rol"] = usuario.rol
            session["nombre"] = usuario.nombre

            if usuario.rol == "tecnico":
                return redirect(url_for("technician.technician_dashboard"))
            else:
                return redirect(url_for("client_interface"))
        else:
            return render_template("login.html", error="Credenciales incorrectas")
    
    return render_template("login.html")

def logout():
    session.clear()
    flash("✅ Sesión cerrada correctamente.", "info")
    return redirect(url_for("index"))