from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from .models import Venta, DetalleVenta
from productos.models import Producto
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.timezone import now
from .models import Venta
from gym.formato import formato_cop
from usuarios.decorators import admin_required
import io
import csv


def reporte_ventas_pdf(request):
    from io import BytesIO
    ventas = Venta.objects.all()

    id_venta = request.GET.get("id_venta")
    fecha = request.GET.get("fecha")
    total_min = request.GET.get("total_min")
    total_max = request.GET.get("total_max")

    if id_venta:
        ventas = ventas.filter(id_venta=id_venta)

    if fecha:
        ventas = ventas.filter(fecha__date=fecha)

    if total_min:
        ventas = ventas.filter(total__gte=total_min)

    if total_max:
        ventas = ventas.filter(total__lte=total_max)

    template = get_template('ventas/reporte_pdf.html')
    html = template.render({
        'ventas': ventas,
        'now': now()
    })

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer)
    
    if pisa_status.err:
        return HttpResponse(f'Error al generar PDF: {pisa_status.err}', status=500)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_ventas.pdf"'
    return response


def reporte_ventas_excel(request):
    ventas = Venta.objects.all()

    id_venta = request.GET.get("id_venta")
    fecha = request.GET.get("fecha")
    total_min = request.GET.get("total_min")
    total_max = request.GET.get("total_max")

    if id_venta:
        ventas = ventas.filter(id_venta=id_venta)
    if fecha:
        ventas = ventas.filter(fecha__date=fecha)
    if total_min:
        ventas = ventas.filter(total__gte=total_min)
    if total_max:
        ventas = ventas.filter(total__lte=total_max)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['REPORTE DE VENTAS'])
    writer.writerow([])
    writer.writerow(['ID', 'Fecha', 'Usuario', 'Plan', 'Total', 'Estado'])

    for v in ventas:
        writer.writerow([
            v.id_venta,
            v.fecha.strftime('%d/%m/%Y %H:%M') if v.fecha else '',
            v.usuario.username if v.usuario else '',
            v.plan.nombre if v.plan else '',
            v.total,
            v.estado
        ])

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_ventas.csv"'
    return response


@login_required
@transaction.atomic
def confirmar_venta(request):

    carrito = request.session.get("carrito", {})

    if not carrito:
        return redirect("ver_carrito")

    errores_stock = []
    for key, item in carrito.items():
        try:
            producto = Producto.objects.get(id_producto=key)
            cantidad_solicitada = int(item["cantidad"])
            if cantidad_solicitada <= 0:
                errores_stock.append(f'"{producto.nombre}": la cantidad debe ser mayor a 0.')
            elif cantidad_solicitada > producto.stock_actual:
                errores_stock.append(
                    f'"{producto.nombre}": solicitaste {cantidad_solicitada}, stock disponible: {producto.stock_actual}.'
                )
            if producto.stock_actual <= 0:
                errores_stock.append(
                    f'"{producto.nombre}" ya no tiene stock disponible.'
                )
        except Producto.DoesNotExist:
            errores_stock.append(f'El producto "{item["nombre"]}" ya no existe.')

    if errores_stock:
        for error in errores_stock:
            messages.error(request, error)
        return redirect("ver_carrito")

    total = 0

    for key, item in carrito.items():
        total += int(item["cantidad"]) * float(item["precio"])

    venta = Venta.objects.create(
        usuario=request.user,
        total=total
    )

    for key, item in carrito.items():

        producto = Producto.objects.get(id_producto=key)

        cantidad = int(item["cantidad"])
        precio = float(item["precio"])
        subtotal = cantidad * precio

        DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=precio,
            subtotal=subtotal
        )

        producto.stock_actual -= cantidad
        producto.save()
        
        # Verificar si el stock quedó bajo y enviar notificación
        from usuarios.models import Notificacion
        Notificacion.notificar_stock_bajo(producto)

        if producto.tiene_maquina and producto.maquina_id:

            from maquinaria.models import Maquinaria

            try:
                maquina = Maquinaria.objects.get(id_maquina=producto.maquina_id)
                maquina.estado = "vendido"
                maquina.motivo_salida = "venta"
                maquina.save()
            except Maquinaria.DoesNotExist:
                pass

    request.session["carrito"] = {}

    messages.success(request, f'¡Compra realizada con éxito! Tu pedido por {formato_cop(total)} ha sido procesado. Venta #{venta.id_venta}.')

    return redirect("catalogo")


@admin_required
def lista_ventas(request):
    ventas = Venta.objects.all().prefetch_related('detalles__producto')
    return render(request, "ventas/lista_ventas.html", {"ventas": ventas})


@admin_required
def detalle_venta(request, id):
    venta = get_object_or_404(Venta, id_venta=id)
    detalles = DetalleVenta.objects.filter(venta=venta)

    return render(request, "ventas/detalle_venta.html", {
        "venta": venta,
        "detalles": detalles
    })

@login_required
def pago_carrito(request):

    carrito = request.session.get("carrito", {})

    if not carrito:
        return redirect("ver_carrito")

    total = 0

    for key, item in carrito.items():
        precio = float(item.get("precio", 0))
        cantidad = int(item.get("cantidad", 0))
        subtotal = precio * cantidad
        item["subtotal"] = subtotal
        total += subtotal

    return render(request, "ventas/pago_carrito.html", {
        "total": total,
        "carrito": carrito
    })


@admin_required
@transaction.atomic
def eliminar_venta(request, id):
    """Elimina una venta de productos y restaura el stock"""
    venta = get_object_or_404(Venta, id_venta=id)

    detalles = DetalleVenta.objects.filter(venta=venta)
    for detalle in detalles:
        producto = detalle.producto
        producto.stock_actual += detalle.cantidad
        producto.save()

        if producto.tiene_maquina and producto.maquina_id:
            from maquinaria.models import Maquinaria
            try:
                maquina = Maquinaria.objects.get(id_maquina=producto.maquina_id)
                maquina.estado = "venta"
                maquina.motivo_salida = ""
                maquina.save()
            except Maquinaria.DoesNotExist:
                pass

    venta.delete()

    messages.success(request, f'Venta #{id} eliminada correctamente. Stock restaurado.')
    return redirect(request.GET.get('next', 'lista_ventas'))
