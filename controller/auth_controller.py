from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models.models import db, Usuario

def index():
    if "usuario_id" in session:
        if session["rol"] == "tecnico":
            return redirect(url_for("technician.technician_dashboard"))
        else:
            return redirect(url_for("client_interface"))
    return render_template("index.html")

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