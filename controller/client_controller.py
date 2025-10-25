from flask import render_template, request
from models.models import Orden
from zoneinfo import ZoneInfo

# Zona horaria de Perú
PERU_TZ = ZoneInfo("America/Lima")

def client_interface():
    # Cualquier usuario puede consultar con código; no forzamos rol
    code = request.args.get("code", "")
    error = None
    order = None
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
                'technician_email': (orden.tecnico.correo if getattr(orden, 'tecnico', None) else None)
            }
    return render_template("clientInterface.html", order=order, error=error)