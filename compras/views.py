
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .models import Compra, DetalleCompra
from proveedores.models import Proveedor
from productos.models import Producto
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.timezone import now
from usuarios.decorators import admin_required


@admin_required
def reporte_compras_pdf(request):
    compras = Compra.objects.all()

    id_compra = request.GET.get("id_compra")
    proveedor = request.GET.get("proveedor")
    fecha = request.GET.get("fecha")
    total_min = request.GET.get("total_min")

    if id_compra:
        compras = compras.filter(id_compra=id_compra)

    if proveedor:
        compras = compras.filter(proveedor__nombre__icontains=proveedor)

    if fecha:
        compras = compras.filter(fecha=fecha)

    if total_min:
        compras = compras.filter(total__gte=total_min)

    template = get_template('compras/reporte_pdf.html')
    html = template.render({
        'compras': compras,
        'now': now()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_compras.pdf"'

    pisa.CreatePDF(html, dest=response)

    return response


@admin_required
def reporte_compras_excel(request):
    """Exporta todas las compras a Excel"""
    import csv
    import io
    
    compras = Compra.objects.all().select_related("proveedor")
    
    proveedor = request.GET.get("proveedor")
    fecha = request.GET.get("fecha")
    total_min = request.GET.get("total_min")
    id_compra = request.GET.get("id_compra")
    
    if proveedor:
        compras = compras.filter(proveedor__nombre__icontains=proveedor)
    if fecha:
        compras = compras.filter(fecha__date=fecha)
    if total_min:
        compras = compras.filter(total__gte=total_min)
    if id_compra:
        compras = compras.filter(id_compra=id_compra)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Proveedor', 'Producto', 'Cantidad', 'Precio Unitario', 'Fecha', 'Total'])
    
    for compra in compras:
        detalle = DetalleCompra.objects.filter(compra=compra).first()
        producto = detalle.producto.nombre if detalle and detalle.producto else '-'
        cantidad = detalle.cantidad if detalle else '-'
        precio = detalle.precio_unitario if detalle else '-'
        
        writer.writerow([
            compra.id_compra,
            compra.proveedor.nombre,
            producto,
            cantidad,
            precio,
            compra.fecha.strftime('%d/%m/%Y') if compra.fecha else '-',
            float(compra.total)
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_compras.csv"'
    
    return response


# ==========================
# LISTA COMPRAS + FILTROS
# ==========================

@admin_required
def lista_compras(request):

    compras = Compra.objects.all().select_related("proveedor")

    proveedor = request.GET.get("proveedor")
    fecha = request.GET.get("fecha")
    total_min = request.GET.get("total_min")
    id_compra = request.GET.get("id_compra")

    if proveedor:
        compras = compras.filter(proveedor__nombre__icontains=proveedor)

    if fecha:
        compras = compras.filter(fecha__date=fecha)

    if total_min:
        compras = compras.filter(total__gte=total_min)

    if id_compra:
        compras = compras.filter(id_compra=id_compra)

    compras_con_detalles = []
    for compra in compras:
        detalle = DetalleCompra.objects.filter(compra=compra).select_related('producto').first()
        compras_con_detalles.append({
            'compra': compra,
            'detalle': detalle,
        })

    # Obtener proveedores para el filtro desplegable
    from proveedores.models import Proveedor
    proveedores = Proveedor.objects.filter(estado='activo').order_by('nombre')

    return render(request, "compras/lista_compras.html", {
        "compras_con_detalles": compras_con_detalles,
        "proveedores": proveedores
    })

# ==========================
# CREAR COMPRA
# ==========================

@admin_required
@transaction.atomic
def crear_compra(request):

    proveedores = Proveedor.objects.filter(estado="activo").prefetch_related('productos')

    if request.method == "POST":

        proveedor_id = request.POST["proveedor"]
        producto_id = request.POST["producto"]
        cantidad = int(request.POST["cantidad"])
        precio_costo = float(request.POST["precio"])
        precio_venta = float(request.POST.get("precio_venta", 0))

        if cantidad <= 0:
            from django.contrib import messages
            messages.error(request, "La cantidad debe ser mayor a 0.")
            return render(request, "compras/form_compra.html", {
                "proveedores": proveedores
            })

        subtotal = cantidad * precio_costo

        compra = Compra.objects.create(
            proveedor_id=proveedor_id,
            total=subtotal
        )

        DetalleCompra.objects.create(
            compra=compra,
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=precio_costo,
            subtotal=subtotal
        )

        producto = Producto.objects.get(id_producto=producto_id)
        producto.stock_actual += cantidad
        producto.precio_costo = precio_costo
        if precio_venta > 0:
            producto.precio_venta = precio_venta
        producto.save()
        
        # Verificar si el stock quedó bajo y enviar notificación
        from usuarios.models import Notificacion
        Notificacion.notificar_stock_bajo(producto)

        return redirect("lista_compras")

    return render(request, "compras/form_compra.html", {
        "proveedores": proveedores
    })


# ==========================
# EDITAR COMPRA
# ==========================

@admin_required
@transaction.atomic
def editar_compra(request, id):

    compra = get_object_or_404(Compra, id_compra=id)

    detalle = DetalleCompra.objects.filter(compra=compra).first()

    if not detalle:
        detalle = DetalleCompra.objects.create(
            compra=compra,
            producto=Producto.objects.first(),
            cantidad=1,
            precio_unitario=0,
            subtotal=0
        )

    proveedores = Proveedor.objects.filter(estado="activo").prefetch_related('productos')

    if request.method == "POST":

        proveedor_id = request.POST["proveedor"]
        compra.proveedor_id = proveedor_id

        producto = Producto.objects.get(
            id_producto=request.POST["producto"]
        )

        nueva_cantidad = int(request.POST["cantidad"])
        precio = float(request.POST["precio"])

        if nueva_cantidad <= 0:
            from django.contrib import messages
            messages.error(request, "La cantidad debe ser mayor a 0.")
            return render(request, "compras/form_compra.html", {
                "compra": compra,
                "detalle": detalle,
                "proveedores": proveedores
            })

        cantidad_anterior = detalle.cantidad

        producto.stock_actual = (
            producto.stock_actual
            - cantidad_anterior
            + nueva_cantidad
        )

        producto.save()

        detalle.producto = producto
        detalle.cantidad = nueva_cantidad
        detalle.precio_unitario = precio
        detalle.subtotal = nueva_cantidad * precio
        detalle.save()

        compra.total = detalle.subtotal
        compra.save()

        return redirect("lista_compras")

    return render(request, "compras/form_compra.html", {
        "compra": compra,
        "detalle": detalle,
        "proveedores": proveedores
    })

# ==========================
# ELIMINAR COMPRA
# ==========================

@admin_required
@transaction.atomic
def eliminar_compra(request, id):

    compra = get_object_or_404(Compra, id_compra=id)

    detalle = DetalleCompra.objects.filter(compra=compra).first()

    if detalle:
        producto = detalle.producto
        producto.stock_actual -= detalle.cantidad
        producto.save()

    compra.delete()

    return redirect("lista_compras")


@admin_required
def ver_detalle_compra(request, id):

    compra = get_object_or_404(Compra, id_compra=id)

    detalles = DetalleCompra.objects.filter(compra=compra)

    return render(request, "compras/detalle_compra.html", {
        "compra": compra,
        "detalles": detalles
    })
