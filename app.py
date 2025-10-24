from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect
from models.models import db, Usuario, Orden
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
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

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
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
                return redirect(url_for("technician_dashboard"))
            else:
                return redirect(url_for("client_interface"))
        else:
            return render_template("login.html", error="Credenciales incorrectas")
    
    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    flash("✅ Sesión cerrada correctamente.", "info")
    return redirect(url_for("index"))

# ---------- CLIENT INTERFACE (seguimiento) ----------
@app.route("/client", methods=["GET"])
def client_interface():
    # Cualquier usuario puede consultar con código; no forzamos rol
    code = request.args.get("code", "")
    error = None
    order = None
    if code:
        order = Orden.query.filter_by(codigo=code).first()
        if not order:
            error = "❌ Código no encontrado"
    return render_template("clientInterface.html", order=order, error=error)

# ---------- TECHNICIAN DASHBOARD ----------
@app.route("/technician", methods=["GET", "POST"])
def technician_dashboard():
    if "rol" not in session or session.get("rol") != "tecnico":
        return redirect(url_for("login"))

    if request.method == "POST":
        # Crear nueva orden desde el dashboard
        clientName = request.form.get("clientName")
        clientPhone = request.form.get("clientPhone")
        clientEmail = request.form.get("clientEmail")
        deviceType = request.form.get("deviceType")
        deviceBrand = request.form.get("deviceBrand")
        deviceModel = request.form.get("deviceModel")
        reportedIssue = request.form.get("reportedIssue")

        # Generar código simple compatible con modelo (codigo)
        codigo = f"ORD-{random.randint(1000,9999)}"
        nueva = Orden(
            codigo=codigo,
            cliente=clientName,
            cliente_telefono=clientPhone,  # Guardar teléfono
            cliente_email=clientEmail,     # Guardar email
            dispositivo=f"{deviceType} {deviceBrand} {deviceModel}".strip(),
            device_type=deviceType,        # Nuevos campos normalizados
            device_brand=deviceBrand,
            device_model=deviceModel,
            falla=reportedIssue,
            estado="RECIBIDO",
            fecha_creacion=datetime.utcnow()
        )
        db.session.add(nueva)
        db.session.commit()
        flash(f"✅ Orden {codigo} creada", "success")
        return redirect(url_for("technician_dashboard"))

    # Stats y listado
    ordenes = Orden.query.order_by(Orden.fecha_creacion.desc()).all()
    
    # Pasar los datos COMPLETOS al template
    orders = [
        {
            'trackingCode': o.codigo,
            'cliente': o.cliente,
            'cliente_telefono': o.cliente_telefono,
            'cliente_email': o.cliente_email,
            'deviceBrand': o.device_brand or o.dispositivo.split(' ')[1] if len(o.dispositivo.split(' '))>1 else o.dispositivo,
            'deviceModel': o.device_model or ' '.join(o.dispositivo.split(' ')[2:]) if len(o.dispositivo.split(' '))>2 else '',
            'status': o.estado,
            'createdAt': o.fecha_creacion.strftime('%d/%m/%Y %H:%M') if o.fecha_creacion else ''
        } for o in ordenes
    ]

    active = request.args.get('tab','create')
    code = request.args.get('code','')
    selected = None
    if active == 'update' and code:
        selected_order = Orden.query.filter_by(codigo=code).first()
        if selected_order:
            selected = {
                'trackingCode': selected_order.codigo,
                'cliente': selected_order.cliente,
                'cliente_telefono': selected_order.cliente_telefono,
                'cliente_email': selected_order.cliente_email,
                'deviceBrand': selected_order.device_brand,
                'deviceModel': selected_order.device_model,
                'dispositivo': selected_order.dispositivo,
                'reportedIssue': selected_order.falla,
                'diagnosis': selected_order.diagnosis,
                'requiredParts': selected_order.required_parts,
                'repairCost': selected_order.repair_cost,
                'status': selected_order.estado
            }

    return render_template("TechnicianDashboard.html", user={'name': session.get('nombre','')}, orders=orders, selected=selected)

# ---------- TECHNICIAN INTERFACE (crear/buscar/actualizar simple) ----------
@app.route("/technician/interface", methods=["GET"])
def technician_interface():
    if "rol" not in session or session.get("rol") != "tecnico":
        return redirect(url_for("login"))

    code = request.args.get('code','')
    order = Orden.query.filter_by(codigo=code).first() if code else None
    return render_template("TechnicianInterface.html", order=order)

# Crear orden desde TechnicianInterface
@app.route("/technician/interface/create", methods=["POST"])
def ti_create_order():
    if "rol" not in session or session.get("rol") != "tecnico":
        return redirect(url_for("login"))
    clientName = request.form.get("clientName")
    clientPhone = request.form.get("clientPhone")
    clientEmail = request.form.get("clientEmail")
    deviceType = request.form.get("deviceType")
    deviceBrand = request.form.get("deviceBrand")
    deviceModel = request.form.get("deviceModel")
    reportedIssue = request.form.get("reportedIssue")

    codigo = f"ORD-{random.randint(1000,9999)}"
    nueva = Orden(
        codigo=codigo,
        cliente=clientName,
        cliente_telefono=clientPhone,
        cliente_email=clientEmail,
        dispositivo=f"{deviceType} {deviceBrand} {deviceModel}".strip(),
        device_type=deviceType,
        device_brand=deviceBrand,
        device_model=deviceModel,
        falla=reportedIssue,
        estado="RECIBIDO",
        fecha_creacion=datetime.utcnow()
    )
    db.session.add(nueva)
    db.session.commit()
    flash(f"✅ Orden {codigo} creada", "success")
    return redirect(url_for('technician_interface', tab='create'))

# Actualizar orden desde TechnicianInterface
@app.route("/technician/interface/update/<string:trackingCode>", methods=["POST"])
def ti_update_order(trackingCode):
    if "rol" not in session or session.get("rol") != "tecnico":
        return redirect(url_for("login"))
    orden = Orden.query.filter_by(codigo=trackingCode).first_or_404()
    
    # Actualizar todos los campos
    orden.estado = request.form.get('status', orden.estado)
    orden.diagnosis = request.form.get('diagnosis', orden.diagnosis)
    orden.required_parts = request.form.get('requiredParts', orden.required_parts)
    orden.repair_cost = request.form.get('repairCost', orden.repair_cost)
    orden.fecha_actualizacion = datetime.utcnow()
    
    db.session.commit()
    flash("✅ Orden actualizada correctamente", 'success')
    return redirect(url_for('technician_dashboard', tab='update', code=trackingCode))

if __name__ == "__main__":
    app.run(debug=True)