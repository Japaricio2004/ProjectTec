from flask import render_template, request, redirect, url_for, flash, session
from models.models import db, Orden, Valoracion
from zoneinfo import ZoneInfo

# Zona horaria de Perú
PERU_TZ = ZoneInfo("America/Lima")

def client_interface():
    # Cualquier usuario puede consultar con código; no forzamos rol
    code = request.args.get("code", "") if request.method == "GET" else request.form.get("code", "")
    error = None
    order = None
    # Guardar valoración si viene por POST
    if request.method == "POST":
        try:
            rating = int(request.form.get("rating", "0"))
        except ValueError:
            rating = 0
        comment = request.form.get("comment")
        if not code:
            error = "Código requerido para registrar valoración"
        else:
            orden = Orden.query.filter_by(codigo=code).first()
            if not orden:
                error = "❌ Código no encontrado"
            elif orden.estado != 'ENTREGADO':
                error = "Solo puedes calificar una orden entregada"
            elif rating < 1 or rating > 5:
                error = "La calificación debe ser de 1 a 5"
            else:
                val = Valoracion.query.filter_by(orden_id=orden.id).first()
                if not val:
                    val = Valoracion(orden_id=orden.id, rating=rating, comentario=comment)
                    db.session.add(val)
                else:
                    val.rating = rating
                    val.comentario = comment
                db.session.commit()
                flash("✅ ¡Gracias por calificar!", "success")
                return redirect(url_for('client_interface', code=code))
    if code:
        orden = Orden.query.filter_by(codigo=code).first()
        if not orden:
            error = "❌ Código no encontrado"
        else:
            # Mapear el estado actual a un número de progreso
            estado_progreso = {
                'RECIBIDO': 20,
                'EN DIAGNÓSTICO': 40,
                'ESPERA DE APROBACIÓN': 60,
                'EN REPARACIÓN': 80,
                'REPARADO': 90,
                'ENTREGADO': 100
            }
            
            # Determinar el color del estado
            estado_color = {
                'RECIBIDO': 'blue',
                'EN DIAGNÓSTICO': 'purple',
                'ESPERA DE APROBACIÓN': 'amber',
                'EN REPARACIÓN': 'indigo',
                'REPARADO': 'green',
                'ENTREGADO': 'gray'
            }
            
            # Crear diccionario con los datos formateados para el template
            # Convertir fechas antiguas (UTC) a hora de Perú
            fecha_creacion_mostrar = orden.fecha_creacion
            if fecha_creacion_mostrar:
                fecha_creacion_mostrar = fecha_creacion_mostrar.replace(tzinfo=ZoneInfo('UTC')).astimezone(PERU_TZ).replace(tzinfo=None)
            
            fecha_actualizacion_mostrar = orden.fecha_actualizacion
            if fecha_actualizacion_mostrar:
                fecha_actualizacion_mostrar = fecha_actualizacion_mostrar.replace(tzinfo=ZoneInfo('UTC')).astimezone(PERU_TZ).replace(tzinfo=None)
            
            # Buscar valoración existente
            valoracion = Valoracion.query.filter_by(orden_id=orden.id).first()

            order = {
                'trackingCode': orden.codigo,
                'deviceType': orden.device_type,
                'deviceBrand': orden.device_brand,
                'deviceModel': orden.device_model,
                'reportedIssue': orden.falla,
                'diagnosis': orden.diagnosis,
                'requiredParts': orden.required_parts,
                'repairCost': orden.repair_cost,
                'status': orden.estado,
                'progress': estado_progreso.get(orden.estado, 0),
                'statusColor': estado_color.get(orden.estado, 'gray'),
                'cliente': orden.cliente,
                'cliente_telefono': orden.cliente_telefono,
                'cliente_email': orden.cliente_email,
                'fecha_creacion': fecha_creacion_mostrar,
                'fecha_actualizacion': fecha_actualizacion_mostrar,
                'technician_name': (orden.tecnico.nombre if getattr(orden, 'tecnico', None) else None),
                'technician_email': (orden.tecnico.correo if getattr(orden, 'tecnico', None) else None),
                'rating': (valoracion.rating if valoracion else None),
                'comment': (valoracion.comentario if valoracion else None),
                'can_rate': (orden.estado == 'ENTREGADO')
            }
    return render_template("clientInterface.html", order=order, error=error)

# --- Nuevo flujo: Client Dashboard clásico (/cliente) ---

def _preparar_orden_para_template(orden: Orden):
    """Mapea atributos del modelo a nombres esperados en clientdashboard.html."""
    # Alias para compatibilidad con el template español
    orden.codigo_seguimiento = orden.codigo
    orden.tipo_dispositivo = orden.device_type
    orden.marca = orden.device_brand
    orden.modelo = orden.device_model
    orden.problema_reportado = orden.falla
    orden.diagnostico = orden.diagnosis
    orden.piezas_necesarias = orden.required_parts
    orden.costo_reparacion = orden.repair_cost
    orden.telefono_cliente = orden.cliente_telefono
    orden.correo_cliente = orden.cliente_email
    # Fechas ya suelen estar en hora local; si vienen antiguas UTC, convertir para mostrar
    if orden.fecha_creacion:
        try:
            orden.fecha_creacion = orden.fecha_creacion.replace(tzinfo=ZoneInfo('UTC')).astimezone(PERU_TZ).replace(tzinfo=None)
        except Exception:
            pass
    if orden.fecha_actualizacion:
        try:
            orden.fecha_actualizacion = orden.fecha_actualizacion.replace(tzinfo=ZoneInfo('UTC')).astimezone(PERU_TZ).replace(tzinfo=None)
        except Exception:
            pass
    return orden

def client_dashboard():
    """Página de búsqueda de orden del cliente (vista clásica)."""
    if "usuario_id" in session and session.get("rol") == "tecnico":
        # Técnicos no deben usar este panel
        return redirect(url_for("technician.technician_dashboard"))
    return render_template("clientdashboard.html", orden=None, codigo_buscado=None)

def cliente_buscar():
    """Procesa el formulario de búsqueda y muestra detalles de la orden."""
    codigo = (request.form.get("codigo_seguimiento", "") or "").strip().upper()
    orden = None
    valoracion = None
    if not codigo:
        flash("Ingresa un código válido", "error")
        return render_template("clientdashboard.html", orden=None, codigo_buscado=codigo)
    o = Orden.query.filter_by(codigo=codigo).first()
    if not o:
        # No encontrada
        return render_template("clientdashboard.html", orden=None, codigo_buscado=codigo)
    # Encontrada: preparar alias y cargar valoración si existe
    orden = _preparar_orden_para_template(o)
    valoracion = Valoracion.query.filter_by(orden_id=o.id).first()
    return render_template("clientdashboard.html", orden=orden, codigo_buscado=codigo, valoracion=valoracion)

def cliente_valorar():
    """Registra o actualiza la valoración del cliente para una orden ENTREGADO."""
    codigo = (request.form.get("codigo", "") or "").strip().upper()
    try:
        rating = int(request.form.get("rating", "0"))
    except ValueError:
        rating = 0
    comentario = request.form.get("comentario")

    o = Orden.query.filter_by(codigo=codigo).first()
    if not o:
        flash("❌ Código no encontrado", "error")
        return render_template("clientdashboard.html", orden=None, codigo_buscado=codigo)
    if o.estado != 'ENTREGADO':
        flash("Solo puedes calificar una orden entregada", "error")
        orden = _preparar_orden_para_template(o)
        return render_template("clientdashboard.html", orden=orden, codigo_buscado=codigo)
    if rating < 1 or rating > 5:
        flash("La calificación debe ser de 1 a 5", "error")
        orden = _preparar_orden_para_template(o)
        return render_template("clientdashboard.html", orden=orden, codigo_buscado=codigo)

    val = Valoracion.query.filter_by(orden_id=o.id).first()
    if not val:
        val = Valoracion(orden_id=o.id, rating=rating, comentario=comentario)
        db.session.add(val)
    else:
        val.rating = rating
        val.comentario = comentario
    db.session.commit()
    flash("✅ ¡Gracias por calificar!", "success")

    orden = _preparar_orden_para_template(o)
    valoracion = Valoracion.query.filter_by(orden_id=o.id).first()
    return render_template("clientdashboard.html", orden=orden, codigo_buscado=codigo, valoracion=valoracion)