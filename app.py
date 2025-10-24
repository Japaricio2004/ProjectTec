from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect
from models.models import db, Usuario, Orden
from werkzeug.security import generate_password_hash, check_password_hash
import random

app = Flask(__name__)
app.secret_key = "clave_secreta_segura"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configurar CSRF
csrf = CSRFProtect()
csrf.init_app(app)

db.init_app(app)

# Crear la base de datos
with app.app_context():
    db.create_all()

# ------------------- RUTAS -------------------

@app.route("/")
def index():
    return render_template("index.html")

# ---------- REGISTRO ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        password = request.form["password"]
        rol = request.form["rol"]

        if Usuario.query.filter_by(correo=correo).first():
            return render_template("register.html", error="El correo ya está registrado")

        hashed = generate_password_hash(password)
        nuevo_usuario = Usuario(nombre=nombre, correo=correo, password=hashed, rol=rol)
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash("✅ Registro exitoso. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"]

        usuario = Usuario.query.filter_by(correo=correo).first()
        if usuario and check_password_hash(usuario.password, password):
            session["usuario_id"] = usuario.id
            session["rol"] = usuario.rol
            session["nombre"] = usuario.nombre

            if usuario.rol == "tecnico":
                return redirect(url_for("panel_tecnico"))
            else:
                return redirect(url_for("panel_cliente"))
        else:
            return render_template("login.html", error="Credenciales incorrectas")
    
    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    flash("✅ Sesión cerrada correctamente.", "info")
    return redirect(url_for("index"))

# ---------- PANEL TÉCNICO ----------
@app.route("/panel_tecnico", methods=["GET", "POST"])
def panel_tecnico():
    if "rol" not in session or session["rol"] != "tecnico":
        return redirect(url_for("login"))

    if request.method == "POST":
        cliente = request.form["cliente"]
        dispositivo = request.form["dispositivo"]
        falla = request.form["falla"]

        codigo = f"ORD-{random.randint(1000,9999)}"
        nueva_orden = Orden(
            codigo=codigo,
            cliente=cliente,
            dispositivo=dispositivo,
            falla=falla,
            estado="RECIBIDO"
        )
        db.session.add(nueva_orden)
        db.session.commit()
        
        flash(f"✅ Orden {codigo} creada exitosamente", "success")

    # Siempre traer las órdenes para mostrarlas abajo
    ordenes = Orden.query.order_by(Orden.fecha_creacion.desc()).all()
    return render_template("panel_tecnico.html", ordenes=ordenes, nombre=session["nombre"])

# ---------- PANEL CLIENTE ----------
@app.route("/panel_cliente", methods=["GET", "POST"])
def panel_cliente():
    if "rol" not in session or session["rol"] != "cliente":
        return redirect(url_for("login"))

    if request.method == "POST":
        codigo = request.form["codigo"]
        orden = Orden.query.filter_by(codigo=codigo).first()
        if orden:
            return render_template("panel_cliente.html", orden=orden, nombre=session["nombre"])
        else:
            return render_template("panel_cliente.html", error="❌ Código no encontrado", nombre=session["nombre"])
    
    return render_template("panel_cliente.html", nombre=session["nombre"])

# ---------- ACTUALIZAR ESTADO DE ORDEN ----------
@app.route("/actualizar_estado/<int:orden_id>", methods=["POST"])
def actualizar_estado(orden_id):
    if "rol" not in session or session["rol"] != "tecnico":
        return redirect(url_for("login"))
    
    orden = Orden.query.get_or_404(orden_id)
    nuevo_estado = request.form["estado"]
    orden.estado = nuevo_estado
    db.session.commit()
    
    flash(f"✅ Estado de orden {orden.codigo} actualizado a {nuevo_estado}", "success")
    return redirect(url_for("panel_tecnico"))

# ---------- ELIMINAR ORDEN ----------
@app.route("/eliminar_orden/<int:orden_id>", methods=["POST"])
def eliminar_orden(orden_id):
    if "rol" not in session or session["rol"] != "tecnico":
        return redirect(url_for("login"))
    
    orden = Orden.query.get_or_404(orden_id)
    db.session.delete(orden)
    db.session.commit()
    
    flash(f"✅ Orden {orden.codigo} eliminada correctamente", "success")
    return redirect(url_for("panel_tecnico"))

if __name__ == "__main__":
    app.run(debug=True)