from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('crear/', views.crear_producto, name='crear_producto'),
    path('editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('toggle/<int:id>/', views.toggle_producto, name='toggle_producto'),
    path('eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('limpiar/', views.limpiar_productos, name='limpiar_productos'),
    path('tienda/', views.catalogo, name='catalogo'),
    path('carrito/', views.ver_carrito, name="ver_carrito"),
    path('carrito/agregar/<int:id>/', views.agregar_carrito, name="agregar_carrito"),
    path('carrito/eliminar/<int:id>/', views.eliminar_carrito, name="eliminar_carrito"),
    path('carrito/sumar/<int:id>/', views.sumar_producto, name="sumar_producto"),
    path('carrito/restar/<int:id>/', views.restar_producto, name="restar_producto"),
    path('carrito/pagar/', views.pago_carrito, name="pago_carrito_producto"),
    path('reporte/pdf/', views.reporte_productos_pdf, name='reporte_pdf'),
    path('reporte/excel/', views.reporte_productos_excel, name='reporte_excel'),
    path('alertas/', views.alertas_stock, name='alertas_stock'),
]