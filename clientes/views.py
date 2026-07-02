from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from usuarios.models import Suscripcion, Perfil, HistorialPeso, MetaUsuario
from usuarios.decorators import admin_required
from ventas.models import Venta as VentaProducto
from ventas.models import Venta, DetalleVenta
from productos.models import Producto
from maquinaria.models import Maquinaria
from .forms import SuscripcionForm
from planes.models import Plan
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField
from datetime import datetime, timedelta
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
import io
import csv


def lista_clientes(request):
    from django.db.models import Q
    
    # Obtener parámetros de filtro
    buscar = request.GET.get('buscar', '').strip()
    plan = request.GET.get('plan', '')
    estado = request.GET.get('estado', '')
    
    # QuerySet base
    clientes = Perfil.objects.filter(rol='cliente').select_related('user')
    
    # Aplicar búsqueda por: nombre, email, username, teléfono, cédula, tarjeta
    if buscar:
        clientes = clientes.filter(
            Q(user__username__icontains=buscar) |
            Q(user__email__icontains=buscar) |
            Q(user__first_name__icontains=buscar) |
            Q(user__last_name__icontains=buscar) |
            Q(telefono__icontains=buscar) |
            Q(cedula__icontains=buscar) |
            Q(tarjeta__icontains=buscar)
        )
    
    # Obtener todos los clientes primero para filtrar por suscripción
    lista_clientes = []
    clientes_all = list(clientes)
    
    for perfil in clientes_all:
        usuario = perfil.user
        suscripciones = Suscripcion.objects.filter(usuario=usuario).select_related('plan')
        suscripcion_activa = suscripciones.filter(activa=True).first()
        
        # Filtrar por plan
        if plan:
            if not suscripciones.filter(plan_id=plan).exists():
                continue
        
        # Filtrar por estado de suscripción
        if estado == "activa" and not suscripcion_activa:
            continue
        if estado == "vencida" and suscripcion_activa:
            continue
        
        lista_clientes.append({
            'perfil': perfil,
            'usuario': usuario,
            'suscripcion_activa': suscripcion_activa,
        })
    
    planes = Plan.objects.all()
    
    # Opciones de estado para el filtro
    opciones_estado = [
        ('activa', 'Activa'),
        ('vencida', 'Vencida'),
    ]
    
    # Preparar filtros custom
    filtros_custom = [
        {
            'name': 'plan',
            'label': 'Plan',
            'opciones': [{'value': p.id, 'label': p.nombre} for p in planes],
            'value': plan
        }
    ]
    
    return render(request, 'clientes/lista_clientes.html', {
        'clientes_data': lista_clientes,
        'planes': planes,
        # Contexto para filtros
        'buscar': buscar,
        'estado': estado,
        'opciones_estado': opciones_estado,
        'filtros_custom': filtros_custom,
        'mostrar_buscar': True,
        'mostrar_fecha': False,
        'mostrar_estado': True,
    })


def ver_cliente(request, id):
    perfil = get_object_or_404(Perfil, id=id)
    usuario = perfil.user
    
    suscripciones = Suscripcion.objects.filter(usuario=usuario).select_related('plan')
    suscripcion_activa = suscripciones.filter(activa=True).first()
    
    ventas_productos = VentaProducto.objects.filter(usuario=usuario)
    total_compras = ventas_productos.aggregate(total=Sum('total'))['total'] or 0
    cantidad_compras = ventas_productos.count()
    
    historial_peso = HistorialPeso.objects.filter(usuario=usuario)[:10]
    metas = MetaUsuario.objects.filter(usuario=usuario)[:10]
    
    return render(request, 'clientes/detalle_cliente.html', {
        'perfil': perfil,
        'usuario': usuario,
        'suscripciones': suscripciones,
        'suscripcion_activa': suscripcion_activa,
        'ventas_productos': ventas_productos[:10],
        'total_compras': total_compras,
        'cantidad_compras': cantidad_compras,
        'historial_peso': historial_peso,
        'metas': metas,
    })


def crear_cliente(request):

    if request.method == "POST":

        form = SuscripcionForm(request.POST)

        if form.is_valid():

            suscripcion = form.save(commit=False)

            # calcular fecha fin automáticamente
            suscripcion.fecha_inicio = timezone.now().date()

            suscripcion.fecha_fin = (
                suscripcion.fecha_inicio +
                timedelta(days=suscripcion.plan.duracion_dias)
            )

            suscripcion.save()

            return redirect('lista_clientes')

    else:
        form = SuscripcionForm()

    return render(request, 'clientes/crear_cliente.html', {
        'form': form
    })


def editar_cliente(request, id):

    cliente = get_object_or_404(Suscripcion, id=id)

    form = SuscripcionForm(request.POST or None, instance=cliente)

    if form.is_valid():
        form.save()
        return redirect('lista_clientes')

    return render(request, 'clientes/editar_cliente.html', {
        'form': form
    })


def eliminar_cliente(request, id):

    cliente = get_object_or_404(Suscripcion, id=id)
    nombre_usuario = cliente.usuario.username

    if request.method == "POST":
        cliente.delete()
        messages.success(request, f'✅ Suscripción de {nombre_usuario} eliminada correctamente.')
        return redirect('lista_clientes')

    return render(request, 'clientes/eliminar_cliente.html', {
        'cliente': cliente
    })


@require_POST
def desactivar_cliente(request, id):
    usuario = get_object_or_404(User, id=id)
    usuario.is_active = False
    usuario.save()
    return redirect('lista_clientes')


@require_POST
def activar_cliente(request, id):
    usuario = get_object_or_404(User, id=id)
    usuario.is_active = True
    usuario.save()
    return redirect('lista_clientes')


from django.contrib import messages

def limpiar_suscripciones(request):
    """Elimina todas las suscripciones de clientes"""
    if request.method == 'POST':
        count = Suscripcion.objects.count()
        Suscripcion.objects.all().delete()
        messages.success(request, f'Se eliminaron {count} suscripciones correctamente.')
    return redirect('lista_clientes')


def limpiar_clientes(request):
    """Elimina todos los clientes (usuarios con rol cliente)"""
    if request.method == 'POST':
        count_perfiles = Perfil.objects.filter(rol='cliente').count()
        Perfil.objects.filter(rol='cliente').delete()
        messages.success(request, f'Se eliminaron {count_perfiles} clientes correctamente.')
    return redirect('lista_clientes')


def reporte_clientes_pdf(request):
    """Genera reporte PDF de clientes"""
    from io import BytesIO
    from django.db.models import Q
    
    clientes = Perfil.objects.filter(rol='cliente').select_related('user')
    
    buscar = request.GET.get('buscar', '').strip()
    plan = request.GET.get('plan', '')
    estado = request.GET.get('estado', '')
    
    # Aplicar mismos filtros que en lista_clientes
    if buscar:
        clientes = clientes.filter(
            Q(user__username__icontains=buscar) |
            Q(user__email__icontains=buscar) |
            Q(user__first_name__icontains=buscar) |
            Q(user__last_name__icontains=buscar) |
            Q(telefono__icontains=buscar) |
            Q(cedula__icontains=buscar) |
            Q(tarjeta__icontains=buscar)
        )
    
    lista_clientes = []
    for perfil in clientes:
        usuario = perfil.user
        suscripciones = Suscripcion.objects.filter(usuario=usuario).select_related('plan')
        suscripcion_activa = suscripciones.filter(activa=True).first()
        
        if plan:
            if not suscripciones.filter(plan_id=plan).exists():
                continue
        
        if estado == "activa" and not suscripcion_activa:
            continue
        if estado == "vencida" and suscripcion_activa:
            continue
        
        lista_clientes.append({
            'perfil': perfil,
            'usuario': usuario,
            'suscripcion_activa': suscripcion_activa,
        })
    
    template = get_template('clientes/reporte_clientes_pdf.html')
    html = template.render({
        'clientes_data': lista_clientes,
        'now': timezone.now()
    })
    
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse(f'Error al generar PDF: {pisa_status.err}', status=500)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_clientes.pdf"'
    return response


def reporte_clientes_excel(request):
    """Exporta reporte de clientes a Excel (CSV)"""
    from django.db.models import Q
    
    clientes = Perfil.objects.filter(rol='cliente').select_related('user')
    
    buscar = request.GET.get('buscar', '').strip()
    plan = request.GET.get('plan', '')
    estado = request.GET.get('estado', '')
    
    # Aplicar mismos filtros
    if buscar:
        clientes = clientes.filter(
            Q(user__username__icontains=buscar) |
            Q(user__email__icontains=buscar) |
            Q(user__first_name__icontains=buscar) |
            Q(user__last_name__icontains=buscar) |
            Q(telefono__icontains=buscar) |
            Q(cedula__icontains=buscar) |
            Q(tarjeta__icontains=buscar)
        )
    
    lista_clientes = []
    for perfil in clientes:
        usuario = perfil.user
        suscripciones = Suscripcion.objects.filter(usuario=usuario).select_related('plan')
        suscripcion_activa = suscripciones.filter(activa=True).first()
        
        if plan:
            if not suscripciones.filter(plan_id=plan).exists():
                continue
        
        if estado == "activa" and not suscripcion_activa:
            continue
        if estado == "vencida" and suscripcion_activa:
            continue
        
        lista_clientes.append({
            'perfil': perfil,
            'usuario': usuario,
            'suscripcion_activa': suscripcion_activa,
        })
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['REPORTE DE CLIENTES'])
    writer.writerow([])
    writer.writerow(['ID', 'Usuario', 'Nombre', 'Email', 'Teléfono', 'Plan', 'Estado Suscripción', 'Fecha Inicio', 'Fecha Fin'])
    
    for c in lista_clientes:
        usuario = c['usuario']
        suscripcion = c['suscripcion_activa']
        
        plan_nombre = suscripcion.plan.nombre if suscripcion else 'Sin plan'
        estado_susc = 'Activa' if suscripcion else 'Sin suscripción'
        fecha_inicio = suscripcion.fecha_inicio.strftime('%d/%m/%Y') if suscripcion and suscripcion.fecha_inicio else '-'
        fecha_fin = suscripcion.fecha_fin.strftime('%d/%m/%Y') if suscripcion and suscripcion.fecha_fin else '-'
        
        writer.writerow([
            usuario.id,
            usuario.username,
            f"{usuario.first_name} {usuario.last_name}".strip() or '-',
            usuario.email,
            c['perfil'].telefono or '-',
            plan_nombre,
            estado_susc,
            fecha_inicio,
            fecha_fin
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_clientes.csv"'
    return response


@admin_required
def dashboard(request):
    now = timezone.now()
    today = now.date()
    start_of_month = today.replace(day=1)
    start_of_week = today - timedelta(days=today.weekday())

    total_usuarios = User.objects.count()
    clientes_activos = Perfil.objects.filter(rol='cliente', user__is_active=True).count()
    clientes_inactivos = Perfil.objects.filter(rol='cliente', user__is_active=False).count()
    ultimos_usuarios = User.objects.order_by('-date_joined')[:5].select_related('perfil')

    total_ventas = Venta.objects.count()
    total_suscripciones = Suscripcion.objects.count()

    ingresos_mes = Venta.objects.filter(
        fecha__year=now.year,
        fecha__month=now.month,
        estado='completada'
    ).aggregate(total=Sum('total'))['total'] or 0

    ingresos_semana = Venta.objects.filter(
        fecha__date__gte=start_of_week,
        estado='completada'
    ).aggregate(total=Sum('total'))['total'] or 0

    costos_mes = DetalleVenta.objects.filter(
        venta__fecha__year=now.year,
        venta__fecha__month=now.month,
        venta__estado='completada'
    ).aggregate(
        total=Sum(
            ExpressionWrapper(F('cantidad') * F('precio_unitario'), output_field=DecimalField())
        )
    )['total'] or 0

    ganancia_mes = ingresos_mes - costos_mes
    ultimas_ventas = Venta.objects.select_related('usuario').order_by('-fecha')[:5]

    top_productos = DetalleVenta.objects.filter(
        venta__fecha__gte=now - timedelta(days=30),
        venta__estado='completada'
    ).values('producto__nombre', 'producto__precio_venta').annotate(
        vendidos=Sum('cantidad')
    ).order_by('-vendidos')[:5]

    total_productos = Producto.objects.count()
    unidades_stock = Producto.objects.aggregate(total=Sum('stock_actual'))['total'] or 0
    stock_bajo = Producto.objects.filter(stock_actual__lt=5).count()
    stock_ok = Producto.objects.filter(stock_actual__gte=5).count()
    productos_sin_stock = Producto.objects.filter(stock_actual__lte=0)[:10]

    total_maquinas = Maquinaria.objects.count()
    maquinas_activas = Maquinaria.objects.filter(estado='activo').count()
    maquinas_reparacion = Maquinaria.objects.filter(estado='reparacion').count()
    lista_maquinas = Maquinaria.objects.all().order_by('-id_maquina')[:10]

    context = {
        'total_usuarios': total_usuarios,
        'clientes_activos': clientes_activos,
        'clientes_inactivos': clientes_inactivos,
        'ultimos_usuarios': ultimos_usuarios,
        'total_ventas': total_ventas,
        'total_suscripciones': total_suscripciones,
        'ingresos_mes': ingresos_mes,
        'ingresos_semana': ingresos_semana,
        'ganancia_mes': ganancia_mes,
        'ultimas_ventas': ultimas_ventas,
        'top_productos': top_productos,
        'total_productos': total_productos,
        'unidades_stock': unidades_stock,
        'stock_bajo': stock_bajo,
        'stock_ok': stock_ok,
        'productos_sin_stock': productos_sin_stock,
        'total_maquinas': total_maquinas,
        'maquinas_activas': maquinas_activas,
        'maquinas_reparacion': maquinas_reparacion,
        'lista_maquinas': lista_maquinas,
    }

    return render(request, 'clientes/dashboard.html', context)