from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['id_producto', 'nombre', 'categoria', 'precio_venta', 'stock_actual', 'estado']
    list_filter = ['estado', 'categoria']
    search_fields = ['nombre', 'categoria']
    list_editable = ['estado']
