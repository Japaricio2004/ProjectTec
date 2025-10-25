from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from zoneinfo import ZoneInfo
import random
from models.models import db, Orden

# Crear Blueprint
technician = Blueprint('technician', __name__)

# Zona horaria de Perú
PERU_TZ = ZoneInfo("America/Lima")

def get_peru_time():
    """Retorna la hora actual en zona horaria de Perú (sin timezone info para SQLite)"""
    return datetime.now(PERU_TZ).replace(tzinfo=None)

# Definir estados válidos del sistema
ESTADOS_ORDEN = [
    'RECIBIDO',
    'EN DIAGNÓSTICO',
    'ESPERA DE APROBACIÓN',
    'EN REPARACIÓN',
    'REPARADO',
    'ENTREGADO'
]

@technician.route("/technician", methods=["GET", "POST"])
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
            cliente_telefono=clientPhone,
            cliente_email=clientEmail,
            dispositivo=f"{deviceType} {deviceBrand} {deviceModel}".strip(),
            device_type=deviceType,
            device_brand=deviceBrand,
            device_model=deviceModel,
            falla=reportedIssue,
            tecnico_id=session.get("usuario_id"),
            estado=ESTADOS_ORDEN[0],  # Siempre inicia en RECIBIDO
            fecha_creacion=get_peru_time()
        )
        db.session.add(nueva)
        db.session.commit()
        flash(f"✅ Orden {codigo} creada", "success")
        return redirect(url_for("technician.technician_dashboard"))

    # Stats y listado
    ordenes = Orden.query.order_by(Orden.fecha_creacion.desc()).all()
    
    # Pasar los datos COMPLETOS al template
    orders = []
    for o in ordenes:
        # Para fechas antiguas (UTC), restar 5 horas. Las nuevas ya están en hora de Perú
        # Detectamos fechas UTC si la hora es muy diferente (aproximación simple)
        fecha_mostrar = o.fecha_creacion
        if fecha_mostrar:
            # Si la fecha parece estar en UTC (hora muy adelantada), convertir
            fecha_mostrar = fecha_mostrar.replace(tzinfo=ZoneInfo('UTC')).astimezone(PERU_TZ).replace(tzinfo=None)
        
        orders.append({
            'trackingCode': o.codigo,
            'cliente': o.cliente,
            'cliente_telefono': o.cliente_telefono,
            'cliente_email': o.cliente_email,
            'deviceBrand': o.device_brand or o.dispositivo.split(' ')[1] if len(o.dispositivo.split(' '))>1 else o.dispositivo,
            'deviceModel': o.device_model or ' '.join(o.dispositivo.split(' ')[2:]) if len(o.dispositivo.split(' '))>2 else '',
            'status': o.estado,
            'createdAt': fecha_mostrar.strftime('%d/%m/%Y %H:%M') if fecha_mostrar else ''
        })
    

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

    return render_template("TechnicianDashboard.html", 
                         user={'name': session.get('nombre','')}, 
                         orders=orders, 
                         selected=selected,
                         estados=ESTADOS_ORDEN)

@technician.route("/technician/interface", methods=["GET"])
def technician_interface():
    if "rol" not in session or session.get("rol") != "tecnico":
        return redirect(url_for("login"))

    code = request.args.get('code','')
    order = Orden.query.filter_by(codigo=code).first() if code else None
    return render_template("TechnicianInterface.html", order=order, estados=ESTADOS_ORDEN)

@technician.route("/technician/interface/create", methods=["POST"])
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
        tecnico_id=session.get("usuario_id"),
        estado=ESTADOS_ORDEN[0],  # Siempre inicia en RECIBIDO
        fecha_creacion=get_peru_time()
    )
    db.session.add(nueva)
    db.session.commit()
    flash(f"✅ Orden {codigo} creada", "success")
    return redirect(url_for('technician.technician_interface', tab='create'))

@technician.route("/technician/interface/update/<string:trackingCode>", methods=["POST"])
def ti_update_order(trackingCode):
    if "rol" not in session or session.get("rol") != "tecnico":
        return redirect(url_for("login"))
    orden = Orden.query.filter_by(codigo=trackingCode).first_or_404()
    
    # Obtener el nuevo estado solicitado
    nuevo_estado = request.form.get('status', orden.estado)
    
    # Validar que el nuevo estado sea válido y siga la secuencia
    if nuevo_estado in ESTADOS_ORDEN:
        indice_actual = ESTADOS_ORDEN.index(orden.estado)
        indice_nuevo = ESTADOS_ORDEN.index(nuevo_estado)
        
        # Solo permitir avanzar un estado a la vez o retroceder en caso necesario
        if indice_nuevo <= indice_actual + 1:
            orden.estado = nuevo_estado
            
            # Actualizar campos adicionales según el estado
            if nuevo_estado == 'EN DIAGNÓSTICO':
                orden.diagnosis = request.form.get('diagnosis', orden.diagnosis)
            elif nuevo_estado == 'ESPERA DE APROBACIÓN':
                orden.required_parts = request.form.get('requiredParts', orden.required_parts)
                orden.repair_cost = request.form.get('repairCost', orden.repair_cost)
            
            orden.fecha_actualizacion = get_peru_time()
            db.session.commit()
            flash(f"✅ Estado actualizado a: {nuevo_estado}", 'success')
        else:
            flash("❌ No se puede saltar estados intermedios", 'error')
    else:
        flash("❌ Estado no válido", 'error')
    
    return redirect(url_for('technician.technician_dashboard', tab='update', code=trackingCode))