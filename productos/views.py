from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .models import Producto, Categoria
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from gym.formato import formato_cop
from usuarios.decorators import admin_required
from django.db.models import Count
import io
import csv


@admin_required
def reporte_productos_pdf(request):
    from io import BytesIO
    productos = Producto.objects.all()

    nombre = request.GET.get("nombre")
    categoria = request.GET.get("categoria")
    estado = request.GET.get("estado")
    precio_max = request.GET.get("precio_max")
    stock_min = request.GET.get("stock_min")

    if nombre:
        productos = productos.filter(nombre__icontains=nombre)

    if categoria:
        productos = productos.filter(categoria__nombre__icontains=categoria)

    if estado:
        productos = productos.filter(estado=estado)

    if precio_max:
        productos = productos.filter(precio_venta__lte=precio_max)

    if stock_min:
        productos = productos.filter(stock_actual__gte=stock_min)

    template = get_template('productos/reporte_pdf.html')
    html = template.render({
    'productos': productos,
    'now': now()
})

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse(f'Error al generar PDF: {pisa_status.err}', status=500)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_productos.pdf"'
    return response


@admin_required
def reporte_productos_excel(request):
    productos = Producto.objects.all()

    nombre = request.GET.get("nombre")
    categoria = request.GET.get("categoria")
    estado = request.GET.get("estado")
    precio_max = request.GET.get("precio_max")
    stock_min = request.GET.get("stock_min")

    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if categoria:
        productos = productos.filter(categoria__nombre__icontains=categoria)
    if estado:
        productos = productos.filter(estado=estado)
    if precio_max:
        productos = productos.filter(precio_venta__lte=precio_max)
    if stock_min:
        productos = productos.filter(stock_actual__gte=stock_min)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['REPORTE DE PRODUCTOS'])
    writer.writerow([])
    writer.writerow(['ID', 'Nombre', 'Categoría', 'Stock', 'Precio Costo', 'Precio Venta', 'Estado'])

    for p in productos:
        writer.writerow([
            p.id_producto,
            p.nombre,
            p.categoria.nombre if p.categoria else '',
            p.stock_actual,
            p.precio_costo,
            p.precio_venta,
            p.estado
        ])

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_productos.csv"'
    return response


@admin_required
def lista_productos(request):

    productos = Producto.objects.all()

    nombre = request.GET.get('nombre')
    categoria = request.GET.get('categoria')
    estado = request.GET.get('estado')
    precio_max = request.GET.get('precio_max')
    stock_min = request.GET.get('stock_min')

    if nombre:
        productos = productos.filter(nombre__icontains=nombre)

    if categoria:
        productos = productos.filter(categoria__nombre__icontains=categoria)

    if estado:
        productos = productos.filter(estado=estado)

    if precio_max:
        productos = productos.filter(precio_venta__lte=precio_max)

    if stock_min:
        productos = productos.filter(stock_actual__gte=stock_min)

    # Obtener categorías únicas para el filtro desplegable
    categorias_unicas = Categoria.objects.values_list('nombre', flat=True).distinct().order_by('nombre')

    return render(request, 'productos/lista_productos.html', {
        'productos': productos,
        'categorias': categorias_unicas
    })


@admin_required
def crear_producto(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        descripcion = request.POST['descripcion']
        categoria = request.POST['categoria']
        precio_costo = request.POST.get('precio_costo', 0)
        precio_venta = request.POST['precio_venta']
        stock_actual = request.POST['stock_actual']
        imagen = request.FILES.get('imagen')
        estado = 'activo' if request.POST.get('estado') else 'inactivo'
        
        try:
            precio_costo = float(precio_costo) if precio_costo else 0
            precio_venta = float(precio_venta)
            stock_actual = int(stock_actual) if stock_actual else 0
        except ValueError:
            messages.error(request, "Los valores numéricos no son válidos.")
            return render(request, 'productos/form_producto.html')
        
        if precio_venta <= 0:
            messages.error(request, "El precio de venta debe ser mayor a 0.")
            return render(request, 'productos/form_producto.html')
        
        if stock_actual < 0:
            messages.error(request, "El stock no puede ser negativo.")
            return render(request, 'productos/form_producto.html')
        
        Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            categoria=categoria,
            precio_costo=precio_costo,
            precio_venta=precio_venta,
            stock_actual=stock_actual,
            imagen=imagen,
            estado=estado
        )

        from usuarios.models import Notificacion
        nuevo_producto = Producto.objects.filter(nombre=nombre).first()
        if nuevo_producto:
            Notificacion.notificar_stock_bajo(nuevo_producto)

        return redirect('lista_productos')

    return render(request, 'productos/form_producto.html')


@admin_required
def editar_producto(request, id):
    producto = get_object_or_404(Producto, id_producto=id)

    if request.method == 'POST':
        producto.nombre = request.POST['nombre']
        producto.descripcion = request.POST['descripcion']
        producto.categoria = request.POST['categoria']
        producto.stock_actual = request.POST['stock_actual']
        producto.precio_costo = request.POST.get('precio_costo', 0)
        producto.precio_venta = request.POST['precio_venta']
        producto.estado = 'activo' if request.POST.get('estado') else 'inactivo'

        if request.FILES.get('imagen'):
            producto.imagen = request.FILES['imagen']

        producto.save()

        from usuarios.models import Notificacion
        Notificacion.notificar_stock_bajo(producto)

        return redirect('lista_productos')

    return render(request, 'productos/form_producto.html', {'producto': producto})


@admin_required
def toggle_producto(request, id):
    producto = Producto.objects.get(id_producto=id)

    if producto.estado == "activo":
        producto.estado = "inactivo"
    else:
        producto.estado = "activo"

    producto.save()

    return redirect('lista_productos')


def catalogo(request):

    categoria_seleccionada = request.GET.get('categoria')

    productos = Producto.objects.filter(estado="activo")

    if categoria_seleccionada:
        productos = productos.filter(categoria__nombre__iexact=categoria_seleccionada)

    categorias = Categoria.objects.annotate(
        total=Count('productos')
    ).order_by('nombre')

    return render(request, "productos/tienda/catalogo.html", {
        "productos": productos,
        "categorias": categorias
    })


@login_required
def agregar_carrito(request, id):

    producto = get_object_or_404(Producto, id_producto=id)

    cantidad = int(request.POST.get("cantidad", 1))

    if cantidad <= 0:
        messages.error(request, "La cantidad debe ser mayor a 0.")
        return redirect('catalogo')

    carrito = request.session.get('carrito', {})

    cantidad_actual_en_carrito = 0
    if str(id) in carrito:
        cantidad_actual_en_carrito = carrito[str(id)]['cantidad']

    cantidad_total = cantidad_actual_en_carrito + cantidad

    if producto.stock_actual <= 0:
        messages.error(request, f'"{producto.nombre}" no tiene stock disponible.')
        return redirect('catalogo')

    if cantidad_total > producto.stock_actual:
        disponible = producto.stock_actual - cantidad_actual_en_carrito
        if disponible <= 0:
            messages.error(request, f'Ya tienes todo el stock disponible de "{producto.nombre}" en el carrito ({producto.stock_actual} unidades).')
        else:
            messages.error(request, f'Solo puedes agregar {disponible} unidad(es) más de "{producto.nombre}". Stock disponible: {producto.stock_actual}, ya tienes {cantidad_actual_en_carrito} en el carrito.')
        return redirect('catalogo')

    if str(id) in carrito:
        carrito[str(id)]['cantidad'] += cantidad
    else:
        carrito[str(id)] = {
            'nombre': producto.nombre,
            'precio': float(producto.precio_venta),
            'cantidad': cantidad,
            'imagen': producto.imagen.url if producto.imagen else ""
        }

    request.session['carrito'] = carrito
    messages.success(request, f'"{producto.nombre}" agregado al carrito.')

    return redirect('catalogo')


@login_required
def eliminar_carrito(request, id):

    carrito = request.session.get('carrito', {})

    if str(id) in carrito:
        del carrito[str(id)]

    request.session['carrito'] = carrito

    return redirect('ver_carrito')


@login_required
def ver_carrito(request):
    carrito = request.session.get("carrito", {})
    total = 0

    for key, item in carrito.items():
        subtotal = float(item["precio"]) * int(item["cantidad"])
        item["subtotal"] = subtotal
        total += subtotal

    return render(request, "productos/tienda/carrito.html", {
        "carrito": carrito,
        "total": total
    })

@login_required
def sumar_producto(request, id):

    carrito = request.session.get('carrito', {})

    if str(id) in carrito:
        producto = Producto.objects.filter(id_producto=id).first()
        cantidad_actual = carrito[str(id)]['cantidad']

        if producto and cantidad_actual >= producto.stock_actual:
            messages.error(request, f'No puedes agregar más de "{producto.nombre}". Stock máximo: {producto.stock_actual}.')
            return redirect('ver_carrito')

        carrito[str(id)]['cantidad'] += 1

    request.session['carrito'] = carrito

    return redirect('ver_carrito')

@login_required
def restar_producto(request, id):

    carrito = request.session.get('carrito', {})

    if str(id) in carrito:

        carrito[str(id)]['cantidad'] -= 1

        if carrito[str(id)]['cantidad'] <= 0:
            del carrito[str(id)]

    request.session['carrito'] = carrito

    return redirect('ver_carrito')


def pago_carrito(request):
    """Vista para procesar el pago del carrito (simulado)"""
    carrito = request.session.get('carrito', {})
    
    if not carrito:
        messages.error(request, 'Tu carrito está vacío.')
        return redirect('catalogo')
    
    total = 0
    for key, item in carrito.items():
        subtotal = float(item["precio"]) * int(item["cantidad"])
        total += subtotal
    
    if request.user.is_authenticated:
        from usuarios.models import Venta
    
    request.session['carrito'] = {}
    
    messages.success(request, f'¡Pago exitoso! Tu pedido por {formato_cop(total)} ha sido procesado. Recibirás un correo de confirmación.')

    return redirect('catalogo')


@admin_required
@transaction.atomic
def eliminar_producto(request, id):
    """Elimina un producto permanentemente"""
    producto = get_object_or_404(Producto, id_producto=id)
    nombre = producto.nombre

    if producto.tiene_maquina and producto.maquina_id:
        from maquinaria.models import Maquinaria
        try:
            maquina = Maquinaria.objects.get(id_maquina=producto.maquina_id)
            maquina.estado = "activo"
            maquina.motivo_salida = ""
            maquina.save()
        except Maquinaria.DoesNotExist:
            pass

    carrito = request.session.get('carrito', {})
    if str(id) in carrito:
        del carrito[str(id)]
        request.session['carrito'] = carrito

    producto.delete()
    messages.success(request, f'Producto "{nombre}" eliminado correctamente.')
    return redirect('lista_productos')


@admin_required
def limpiar_productos(request):
    """Elimina todos los productos"""
    if request.method == 'POST':
        count = Producto.objects.count()
        Producto.objects.all().delete()
        messages.success(request, f'Se eliminaron {count} productos correctamente.')
    return redirect('lista_productos')


@admin_required
def alertas_stock(request):
    """Muestra productos con stock bajo"""
    from django.conf import settings
    
    stock_minimo = getattr(settings, 'STOCK_MINIMO_ALERTA', 10)
    stock_critico = getattr(settings, 'STOCK_CRITICO_ALERTA', 3)
    
    productos_criticos = Producto.objects.filter(
        estado='activo',
        stock_actual__lte=stock_critico
    ).order_by('stock_actual')
    
    productos_bajos = Producto.objects.filter(
        estado='activo',
        stock_actual__gt=stock_critico,
        stock_actual__lte=stock_minimo
    ).order_by('stock_actual')
    
    return render(request, 'productos/alertas_stock.html', {
        'productos_criticos': productos_criticos,
        'productos_bajos': productos_bajos,
        'stock_minimo': stock_minimo,
        'stock_critico': stock_critico
    })
