import os
import logging
import random
import requests

from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

from xhtml2pdf import pisa

logger = logging.getLogger(__name__)


def obtener_frase_motivacional():
    """Función de compatibilidad -.delega a api.frases"""
    from api.frases import obtener_frase_motivacional as fn
    return fn()


# Plantillas que existen con objetivo
PLANTILLAS_CON_OBJETIVO = {
    'rutinas/rutina_1_mes': ['bajar_peso', 'mantener', 'subir_masa', 'definir', 'subir_masa_perder_grasa', 'cardio'],
    'rutinas/rutina_6_meses': ['bajar_peso', 'mantener', 'subir_masa', 'definir', 'subir_masa_perder_grasa', 'cardio'],
    'rutinas/rutina_1_ano': ['bajar_peso', 'mantener', 'subir_masa', 'definir', 'subir_masa_perder_grasa', 'cardio'],
    'rutinas/rutina_1_dia': [],
}

# Mapeo de nuevos objetivos a plantillas existentes
# Los nuevos tipos de objetivo usan las plantillas existentes más cercanas
OBJETIVO_A_PLANTILLA = {
    'bajar_peso': 'bajar_peso',
    'subir_masa': 'subir_masa',
    'mantener': 'mantener',
    'definir': 'definir',  # Nueva plantilla específica para definir
    'subir_masa_perder_grasa': 'subir_masa_perder_grasa',  # Nueva plantilla específica
    'cardio': 'cardio',  # Nueva plantilla específica para cardio
}


def obtener_objetivo_usuario(usuario):
    """
    Calcula el objetivo del usuario basado en su peso, estatura y edad.
    Retorna: 'bajar_peso', 'mantener', 'subir_masa'
    """
    print(f"=== CALCULANDO OBJETIVO PARA: {usuario.username} ===")
    
    # Importar aquí para evitar problemas de importación circular
    from usuarios.models import Perfil
    
    try:
        # Hacer consulta directa para obtener datos actualizados de la BD
        perfil = Perfil.objects.get(user=usuario)
    except Perfil.DoesNotExist:
        print("DEBUG: No existe perfil para usuario (DoesNotExist)")
        return 'mantener'
    except Exception as e:
        print(f"DEBUG: Error obteniendo perfil: {e}")
        return 'mantener'
    
    peso = perfil.peso
    estatura = perfil.estatura
    edad = perfil.edad
    
    print(f"DEBUG - Peso BD: {peso}, Estatura BD: {estatura}, Edad BD: {edad}")
    
    # Si no tiene datos, usar objetivo por defecto
    if not peso or not estatura:
        print("DEBUG: No hay datos de peso/estatura, retornando mantener")
        return 'mantener'
    
    # Calcular IMC
    try:
        imc = float(peso) / (float(estatura) ** 2)
        print(f"DEBUG - IMC calculado: {imc:.2f}")
    except Exception as e:
        print(f"DEBUG: Error calculando IMC: {e}")
        return 'mantener'
    
    # Clasificación según IMC
    # Bajo peso: < 18.5
    # Normal: 18.5 - 24.9
    # Sobrepeso: 25 - 29.9
    # Obesidad: >= 30
    
    if imc < 18.5:
        print("DEBUG: IMC < 18.5 -> subir_masa")
        return 'subir_masa'  # Bajo peso - necesita subir masa muscular
    elif imc < 25:
        print("DEBUG: IMC 18.5-24.9 -> mantener")
        return 'mantener'  # Peso normal - mantener
    elif imc < 30:
        print("DEBUG: IMC 25-29.9 -> bajar_peso")
        return 'bajar_peso'  # Sobrepeso
    else:
        print("DEBUG: IMC >= 30 -> bajar_peso")
        return 'bajar_peso'  # Obesidad - prioridad bajar de peso


def obtener_template_rutina(plan, usuario=None, objetivo_seleccionado=None):
    """
    Retorna la plantilla HTML según el tipo de plan y objetivo del usuario.
    Si no hay tipo definido, usa duracion_dias como fallback.
    Si hay datos del usuario y existe la plantilla con objetivo, la usa.
    
    Args:
        plan: El plan de suscripción
        usuario: El usuario (opcional, para calcular objetivo automático)
        objetivo_seleccionado: El objetivo elegido por el cliente (si existe, tiene prioridad)
    """
    
    # Determinar el objetivo: primero el seleccionado por el cliente, luego el calculado
    objetivo = objetivo_seleccionado
    if not objetivo and usuario:
        objetivo = obtener_objetivo_usuario(usuario)
    
    # Primero intentar usar el campo 'tipo' si existe
    tipo = getattr(plan, 'tipo', None)
    duracion = getattr(plan, 'duracion_dias', 0)
    
    if tipo:
        if tipo == "1_dia":
            # Para plan de 1 día, usar la plantilla simple (no hay versión profesional)
            return "rutinas/rutina_1_dia.html"
        elif tipo == "1_mes":
            base_template = "rutinas/rutina_1_mes"
        elif tipo == "6_meses":
            base_template = "rutinas/rutina_6_meses"
        elif tipo == "1_ano":
            base_template = "rutinas/rutina_1_ano"
        elif tipo == "personalizado":
            # Para planes personalizados, usar la duración exacta en días
            # y mapear a la plantilla más cercana
            if duracion <= 30:
                base_template = "rutinas/rutina_1_mes"
            elif duracion <= 60:
                # 2 meses - usar plantilla de 1 mes
                base_template = "rutinas/rutina_1_mes"
            elif duracion <= 90:
                # 3 meses - usar plantilla de 1 mes
                base_template = "rutinas/rutina_1_mes"
            elif duracion <= 180:
                base_template = "rutinas/rutina_6_meses"
            elif duracion <= 270:
                # 9 meses - usar plantilla de 6 meses
                base_template = "rutinas/rutina_6_meses"
            elif duracion <= 365:
                base_template = "rutinas/rutina_1_ano"
            else:
                # Mayor a 1 año - usar plantilla de 1 año
                base_template = "rutinas/rutina_1_ano"
        else:
            base_template = "rutinas/rutina_1_mes"
    else:
        # Fallback: usar duracion_dias si no hay tipo
        if duracion <= 1:
            base_template = "rutinas/rutina_1_dia"
        elif duracion <= 30:
            base_template = "rutinas/rutina_1_mes"
        elif duracion <= 180:
            base_template = "rutinas/rutina_6_meses"
        else:
            base_template = "rutinas/rutina_1_ano"
    
    print(f"DEBUG obtener_template - Base template: {base_template}")
    
    # Si hay un objetivo seleccionado, mapear a la plantilla correcta
    if objetivo:
        objetivo_mapeado = OBJETIVO_A_PLANTILLA.get(objetivo, objetivo)
        
        # Si tenemos el objetivo del usuario Y existe la plantilla con ese objetivo, usarla
        if objetivo_mapeado in PLANTILLAS_CON_OBJETIVO.get(base_template, []):
            template_con_objetivo = f"{base_template}_{objetivo_mapeado}_profesional.html"
            return template_con_objetivo
    
    # Si no existe con objetivo, usar la base profesional si existe
    return f"{base_template}_profesional.html"



def generar_rutina(usuario, plan, objetivo_seleccionado=None):
    """
    Genera el PDF de la rutina usando HTML
    
    Args:
        usuario: El usuario que recibirá la rutina
        plan: El plan de suscripción
        objetivo_seleccionado: El objetivo elegido por el cliente (opcional)
    """

    template = obtener_template_rutina(plan, usuario, objetivo_seleccionado)
    
    # Obtener objetivo para el contexto (primero el seleccionado, luego el calculado)
    objetivo = objetivo_seleccionado
    if not objetivo:
        objetivo = obtener_objetivo_usuario(usuario)
    
    # Obtener perfil del usuario
    try:
        perfil = usuario.perfil
    except:
        perfil = None
    
    # Calcular la duración real del plan en meses
    duracion_dias = getattr(plan, 'duracion_dias', 0)
    
    if duracion_dias > 0:
        duracion_meses = duracion_dias / 30.0
        duracion_meses = int(duracion_meses)
        if duracion_meses < 1:
            duracion_meses = 1
    else:
        duracion_meses = 1

    context = {
        "usuario": usuario,
        "plan": plan,
        "objetivo": objetivo,
        "perfil": perfil,
        "duracion_real_meses": duracion_meses,
        "duracion_real_dias": duracion_dias,
        "tipo_plan": getattr(plan, 'tipo', 'desconocido'),
    }

    html = render_to_string(template, context)

    # Asegurar que el directorio media existe
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    
    ruta = os.path.join(settings.MEDIA_ROOT, f"rutina_{usuario.id}.pdf")

    with open(ruta, "wb") as pdf_file:
        result = pisa.CreatePDF(html, dest=pdf_file)
        if result.err:
            raise Exception(f"Error al generar PDF: {result.err}")

    return ruta



def enviar_rutina_correo(usuario, plan, objetivo_seleccionado=None):
    """
    Envía la rutina en PDF al correo del usuario
    Usa rutinas de la base de datos si existen, si no usa el sistema legacy
    
    Args:
        usuario: El usuario que recibirá la rutina
        plan: El plan de suscripción
        objetivo_seleccionado: El objetivo elegido por el cliente (opcional)
        
    Returns:
        tuple: (exito: bool, mensaje: str)
    """

    if not usuario.email:
        return False, "El usuario no tiene correo electrónico registrado."

    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return False, "El servidor de correo no está configurado. Contacta al administrador."

    try:
        from usuarios.models import Perfil, Rutina, Ejercicio
        try:
            perfil = getattr(usuario, 'perfil', None)
            if not perfil:
                perfil = Perfil.objects.get(user=usuario)
            peso = perfil.peso
            estatura = perfil.estatura
            edad = perfil.edad
        except:
            peso = None
            estatura = None
            edad = None
        
        objetivo = objetivo_seleccionado
        if not objetivo:
            objetivo = obtener_objetivo_usuario(usuario)
        
        rutinas_db = Rutina.objects.filter(activa=True)
        
        if rutinas_db.exists():
            return enviar_rutina_db_correo(usuario, rutinas_db.first(), peso, estatura, edad, objetivo, plan)
        else:
            pdf = generar_rutina(usuario, plan, objetivo_seleccionado)
            return enviar_rutina_legacy_correo(usuario, plan, peso, estatura, edad, objetivo, pdf)

    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower():
            return False, "Error de autenticación del correo. Contacta al administrador."
        elif "connection" in error_msg.lower():
            return False, "No se pudo conectar al servidor de correo."
        return False, f"Error al enviar correo: {error_msg}"


def enviar_rutina_db_correo(usuario, rutina, peso, estatura, edad, objetivo, plan):
    """Envía una rutina desde la base de datos con HTML atractivo"""
    ejercicios_por_dia = rutina.get_ejercicios_por_dia()
    
    dias_html = ""
    dias_orden = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    nombres_dias = {'lunes': 'Lunes', 'martes': 'Martes', 'miercoles': 'Miércoles', 'jueves': 'Jueves', 'viernes': 'Viernes', 'sabado': 'Sábado', 'domingo': 'Domingo'}
    
    for dia in dias_orden:
        ejercicios = ejercicios_por_dia.get(dia, [])
        if ejercicios:
            dias_html += f"""
            <tr style="background: linear-gradient(135deg, #DC3545, #A71D2A);">
                <td colspan="5" style="padding: 12px; color: white; font-weight: bold; text-align: center;">
                    📅 {nombres_dias.get(dia, dia.upper())}
                </td>
            </tr>
            """
            for i, ejercicio in enumerate(ejercicios, 1):
                dias_html += f"""
                <tr style="border-bottom: 1px solid #444;">
                    <td style="padding: 10px; color: #DC3545; font-weight: bold;">{i}</td>
                    <td style="padding: 10px; color: #fff;">{ejercicio.nombre}</td>
                    <td style="padding: 10px; text-align: center;"><span style="background: #DC3545; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px;">{ejercicio.series} series</span></td>
                    <td style="padding: 10px; text-align: center;"><span style="background: #0d6efd; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px;">{ejercicio.repeticiones}</span></td>
                    <td style="padding: 10px; text-align: center; color: #aaa;"><i class="fas fa-clock"></i> {ejercicio.descanso}s</td>
                </tr>
                """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: #1a1a1a; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #2d2d2d; border-radius: 15px; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #DC3545, #A71D2A); padding: 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 28px; }}
            .header p {{ color: #ffcccc; margin: 10px 0 0 0; }}
            .content {{ padding: 20px; }}
            .user-info {{ background: #1a1a1a; border-radius: 10px; padding: 15px; margin-bottom: 20px; }}
            .user-info h3 {{ color: #DC3545; margin: 0 0 10px 0; font-size: 16px; }}
            .user-info p {{ color: #aaa; margin: 5px 0; font-size: 14px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            .rutina-title {{ color: white; font-size: 20px; margin-bottom: 15px; text-align: center; }}
            .footer {{ background: #1a1a1a; padding: 20px; text-align: center; color: #888; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏋️ Tu Rutina GYM XTREME</h1>
                <p>¡Felicitaciones por tu compra!</p>
            </div>
            <div class="content">
                <div class="user-info">
                    <h3>📊 Datos del Cliente</h3>
                    <p><strong>Nombre:</strong> {usuario.first_name or usuario.username}</p>
                    <p><strong>Plan:</strong> {plan.nombre}</p>
                    <p><strong>Peso:</strong> {peso or 'No registrado'} kg</p>
                    <p><strong>Estatura:</strong> {estatura or 'No registrada'} m</p>
                    <p><strong>Objetivo:</strong> {objetivo or 'General'}</p>
                </div>
                
                <h2 class="rutina-title">💪 {rutina.nombre}</h2>
                <p style="color: #aaa; text-align: center; margin-bottom: 20px;">{rutina.descripcion}</p>
                
                <table>
                    {dias_html}
                </table>
                
                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #DC3545; font-size: 18px; font-weight: bold;">¡DISCLAIMER!</p>
                    <p style="color: #888; font-size: 14px;">
                        Esta rutina es una guía general. Consulta a un profesional antes de comenzar.<br>
                        Escucha a tu cuerpo y descansa cuando sea necesario.
                    </p>
                </div>
            </div>
            <div class="footer">
                <p>GYM XTREME - Transformando cuerpos, cambiando vidas</p>
                <p>Este correo fue enviado automáticamente</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        email = EmailMessage(
            f"🏋️ Tu Rutina Personalizada - {rutina.nombre}",
            html_content,
            settings.EMAIL_HOST_USER,
            [usuario.email]
        )
        email.content_subtype = "html"
        result = email.send(fail_silently=True)
        
        if result > 0:
            return True, f"Rutina enviada a {usuario.email}"
        return False, "No se pudo enviar el correo. Intenta de nuevo."
    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "smtplib.SMTPAuthenticationError" in error_msg:
            return False, "Error de autenticación. Usa App Password de Gmail."
        elif "connection" in error_msg.lower():
            return False, "No se pudo conectar al servidor de correo."
        return False, f"Error al enviar correo: {error_msg}"


def enviar_rutina_legacy_correo(usuario, plan, peso, estatura, edad, objetivo, pdf):
    """Envía una rutina usando el sistema legacy (PDF)"""
    info_usuario = f"""Hola {usuario.username},

Gracias por adquirir el plan: {plan.nombre}

--- TUS DATOS ---
Peso: {peso} kg
Estatura: {estatura} m
Edad: {edad} años
Objetivo: {objetivo}
-----------------

Adjuntamos tu rutina personalizada según tu plan y objetivo.

¡Disciplina y constancia! No pares nunca.

Saludos,
Equipo Gym Xtreme
"""

    try:
        email = EmailMessage(
            f"Tu rutina personalizada - {plan.nombre}",
            info_usuario,
            settings.EMAIL_HOST_USER,
            [usuario.email]
        )
        
        email.attach_file(pdf)
        result = email.send(fail_silently=True)
        
        if result > 0:
            return True, f"Rutina enviada a {usuario.email}"
        return False, "No se pudo enviar el correo. Intenta de nuevo."
    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "smtplib.SMTPAuthenticationError" in error_msg:
            return False, "Error de autenticación. Usa App Password de Gmail."
        elif "connection" in error_msg.lower():
            return False, "No se pudo conectar al servidor de correo."
        return False, f"Error al enviar correo: {error_msg}"


def obtener_rutina_activa(usuario):
    """Obtiene la rutina de la suscripción activa del usuario"""
    from usuarios.models import Suscripcion
    from django.utils import timezone
    
    suscripcion = Suscripcion.objects.filter(
        usuario=usuario,
        fecha_fin__gte=timezone.now().date()
    ).first()
    
    if suscripcion and suscripcion.objetivo_rutina:
        return suscripcion.objetivo_rutina
    return None


NOMBRES_RUTINA = {
    'bajar_peso': '🔥 Bajar de Peso',
    'subir_masa': '💪 Subir Masa Muscular',
    'mantener': '⚖️ Mantener Peso',
    'definir': '🥷 Definir Musculatura',
    'cardio': '❤️ Cardio y Resistencia',
    'subir_masa_perder_grasa': '⚡ Subir Masa y Perder Grasa',
}


def analizar_progreso(usuario):
    """
    Analiza el progreso del usuario y genera alertas inteligentes.
    
    Returns:
        dict con:
        - alertas: lista de alertas ({tipo, icono, mensaje, color})
        - recomendacion: texto de recomendación actual
        - rutina_actual: la rutina de la suscripción activa
        - tendencia: 'bajando', 'subiendo', 'estable'
        - imc_anterior: IMC del registro anterior
        - imc_actual: IMC del registro más reciente
        - cambio_categoria: bool si cambió de categoría IMC
        - progreso_meta: porcentaje de avance hacia la meta (si existe)
    """
    from usuarios.models import HistorialPeso, MetaUsuario, Suscripcion
    from django.utils import timezone
    
    resultado = {
        'alertas': [],
        'recomendacion': None,
        'rutina_actual': None,
        'rutina_actual_nombre': None,
        'tendencia': None,
        'imc_anterior': None,
        'imc_actual': None,
        'cambio_categoria': False,
        'progreso_meta': None,
        'peso_objetivo': None,
    }
    
    # Obtener rutina activa
    rutina = obtener_rutina_activa(usuario)
    if rutina:
        resultado['rutina_actual'] = rutina
        resultado['rutina_actual_nombre'] = NOMBRES_RUTINA.get(rutina, rutina)
    
    # Obtener registros de peso
    registros = list(HistorialPeso.objects.filter(usuario=usuario).order_by('-fecha')[:10])
    
    if len(registros) < 1:
        return resultado
    
    ultimo = registros[0]
    imc_actual = float(ultimo.imc) if ultimo.imc else None
    peso_actual = float(ultimo.peso)
    resultado['imc_actual'] = imc_actual
    
    # Clasificación actual
    def get_cat(imc):
        if imc is None: return None
        if imc < 18.5: return 'bajo_peso'
        if imc < 25: return 'normal'
        if imc < 30: return 'sobrepeso'
        return 'obesidad'
    
    cat_actual = get_cat(imc_actual)
    
    # ===== ANÁLISIS DE TENDENCIA =====
    if len(registros) >= 2:
        anterior = registros[1]
        imc_anterior = float(anterior.imc) if anterior.imc else None
        peso_anterior = float(anterior.peso)
        cat_anterior = get_cat(imc_anterior)
        resultado['imc_anterior'] = imc_anterior
        
        diferencia_peso = round(peso_actual - peso_anterior, 1)
        diferencia_imc = round(imc_actual - imc_anterior, 1) if (imc_actual and imc_anterior) else 0
        
        # Detectar tendencia
        if diferencia_peso < -0.3:
            resultado['tendencia'] = 'bajando'
        elif diferencia_peso > 0.3:
            resultado['tendencia'] = 'subiendo'
        else:
            resultado['tendencia'] = 'estable'
        
        # ===== ALERTAS DE CAMBIO =====
        
        # Alerta: cambio de categoría IMC
        if cat_actual != cat_anterior and cat_actual and cat_anterior:
            resultado['cambio_categoria'] = True
            if cat_actual == 'normal':
                resultado['alertas'].append({
                    'tipo': 'exito',
                    'icono': 'fa-trophy',
                    'mensaje': f'¡INCREÍBLE! Tu IMC pasó de {imc_anterior} a {imc_actual}. Ahora estás en PESO NORMAL. ¡Logro desbloqueado!',
                    'color': '#198754',
                })
            elif cat_anterior == 'obesidad' and cat_actual == 'sobrepeso':
                resultado['alertas'].append({
                    'tipo': 'exito',
                    'icono': 'fa-arrow-down',
                    'mensaje': f'¡Excelente progreso! Saliste de obesidad. Tu IMC bajó de {imc_anterior} a {imc_actual}. ¡Sigue así!',
                    'color': '#198754',
                })
            elif cat_anterior == 'sobrepeso' and cat_actual == 'bajo_peso':
                resultado['alertas'].append({
                    'tipo': 'advertencia',
                    'icono': 'fa-exclamation-triangle',
                    'mensaje': f'Tu IMC bajó demasiado ({imc_actual}). Ahora estás en bajo peso. Considera cambiar a una rutina de subir masa.',
                    'color': '#ffc107',
                })
            else:
                resultado['alertas'].append({
                    'tipo': 'info',
                    'icono': 'fa-info-circle',
                    'mensaje': f'Tu categoría IMC cambió: {cat_anterior} → {cat_actual} (IMC {imc_actual})',
                    'color': '#0d6efd',
                })
        
        # Alerta: pérdida significativa de peso
        if diferencia_peso <= -1:
            resultado['alertas'].append({
                'tipo': 'exito',
                'icono': 'fa-fire',
                'mensaje': f'Has perdido {abs(diferencia_peso)} kg desde tu último registro. ¡Vas por buen camino!',
                'color': '#198754',
            })
        
        # Alerta: ganancia significativa de peso
        if diferencia_peso >= 1:
            if rutina == 'bajar_peso':
                resultado['alertas'].append({
                    'tipo': 'advertencia',
                    'icono': 'fa-exclamation-circle',
                    'mensaje': f'Tu peso subió {diferencia_peso} kg. Revisa tu alimentación y constancia en la rutina.',
                    'color': '#ffc107',
                })
            elif rutina == 'subir_masa':
                resultado['alertas'].append({
                    'tipo': 'exito',
                    'icono': 'fa-dumbbell',
                    'mensaje': f'Has ganado {diferencia_peso} kg. ¡Tu masa muscular está creciendo!',
                    'color': '#198754',
                })
        
        # Alerta: IMC se acerca al normal
        if imc_actual and imc_anterior:
            if cat_actual != 'normal':
                if imc_actual < imc_anterior and cat_actual == 'sobrepeso' and imc_actual < 27:
                    resultado['alertas'].append({
                        'tipo': 'motivacion',
                        'icono': 'fa-bullseye',
                        'mensaje': f'Tu IMC es {imc_actual}. ¡Estás a solo {round(imc_actual - 24.9, 1)} puntos de llegar a peso normal!',
                        'color': '#DC3545',
                    })
    
    # ===== RECOMENDACIÓN BASADA EN IMC ACTUAL =====
    if imc_actual:
        if imc_actual < 18.5:
            recomendada = 'subir_masa'
            resultado['recomendacion'] = 'Tu IMC indica bajo peso. Te recomendamos una rutina de subir masa muscular con enfoque en alimentación.'
        elif imc_actual < 25:
            recomendada = 'mantener'
            resultado['recomendacion'] = 'Tu IMC está en rango normal. Enfócate en mantener tu peso y tonificar tu cuerpo.'
        elif imc_actual < 30:
            recomendada = 'bajar_peso'
            resultado['recomendacion'] = 'Tu IMC indica sobrepeso. Te recomendamos combinar cardio con entrenamiento de fuerza para quemar grasa.'
        else:
            recomendada = 'bajar_peso'
            resultado['recomendacion'] = 'Tu IMC indica obesidad. Prioriza bajar de peso gradualmente con cardio y alimentación balanceada.'
        
        # Alerta si la rutina actual no coincide con la recomendada
        if rutina and rutina != recomendada and not resultado['cambio_categoria']:
            nombre_recomendada = NOMBRES_RUTINA.get(recomendada, recomendada)
            resultado['alertas'].append({
                'tipo': 'sugerencia',
                'icono': 'fa-lightbulb',
                'mensaje': f'Tu IMC actual ({imc_actual}) sugiere que "{nombre_recomendada}" sería más adecuada para ti. Considera cambiar de rutina en tu próxima compra.',
                'color': '#ff6b00',
            })
    
    # ===== PROGRESO HACIA META =====
    meta_activa = MetaUsuario.objects.filter(usuario=usuario, estado='activa').first()
    if meta_activa and meta_activa.peso_objetivo:
        resultado['peso_objetivo'] = float(meta_activa.peso_objetivo)
        
        # Buscar el primer registro para calcular progreso total
        primer_registro = HistorialPeso.objects.filter(usuario=usuario).order_by('fecha').first()
        if primer_registro:
            peso_inicial = float(primer_registro.peso)
            peso_meta = float(meta_activa.peso_objetivo)
            
            if peso_inicial != peso_meta:
                progreso = abs((peso_actual - peso_inicial) / (peso_meta - peso_inicial)) * 100
                progreso = min(round(progreso, 0), 100)
                resultado['progreso_meta'] = progreso
                
                # Alerta de meta alcanzada
                if (peso_meta <= peso_inicial and peso_actual <= peso_meta) or \
                   (peso_meta >= peso_inicial and peso_actual >= peso_meta):
                    resultado['alertas'].append({
                        'tipo': 'exito',
                        'icono': 'fa-trophy',
                        'mensaje': f'¡FELICIDADES! Alcanzaste tu meta de {peso_meta} kg. Tu peso actual es {peso_actual} kg.',
                        'color': '#FFD700',
                    })
                elif progreso >= 75:
                    resultado['alertas'].append({
                        'tipo': 'motivacion',
                        'icono': 'fa-rocket',
                        'mensaje': f'¡Estás al {int(progreso)}% de tu meta! Solo te faltan {round(abs(peso_actual - peso_meta), 1)} kg. ¡No te detengas!',
                        'color': '#DC3545',
                    })
                elif progreso >= 50:
                    resultado['alertas'].append({
                        'tipo': 'motivacion',
                        'icono': 'fa-chart-line',
                        'mensaje': f'Vas al {int(progreso)}% de tu meta. ¡Ya pasaste la mitad del camino!',
                        'color': '#0d6efd',
                    })
    
    # ===== COMPARACIÓN CON PRIMER REGISTRO =====
    primer = registros[-1] if len(registros) >= 2 else None
    if primer:
        diferencia_total = round(peso_actual - float(primer.peso), 1)
        if abs(diferencia_total) >= 5:
            if diferencia_total < 0:
                resultado['alertas'].append({
                    'tipo': 'exito',
                    'icono': 'fa-medal',
                    'mensaje': f'Has perdido {abs(diferencia_total)} kg desde que empezaste. ¡Transformación impresionante!',
                    'color': '#198754',
                })
            else:
                if rutina == 'subir_masa':
                    resultado['alertas'].append({
                        'tipo': 'exito',
                        'icono': 'fa-medal',
                        'mensaje': f'Has ganado {diferencia_total} kg de masa desde que empezaste. ¡Buen trabajo!',
                        'color': '#198754',
                    })
    
    return resultado