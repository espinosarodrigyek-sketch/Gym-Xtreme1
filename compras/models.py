from django.db import models
from proveedores.models import Proveedor
from productos.models import Producto


class Compra(models.Model):
    """Modelo para registrar compras a proveedores"""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('recibida', 'Recibida'),
    ]

    id_compra = models.BigAutoField(primary_key=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='compras')
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    notas = models.TextField(blank=True, null=True, help_text="Notas adicionales de la compra")

    class Meta:
        db_table = "compras"
        ordering = ['-fecha']
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'

    def __str__(self):
        return f"Compra #{self.id_compra} - {self.proveedor.nombre} - {self.fecha.strftime('%d/%m/%Y')}"


class DetalleCompra(models.Model):
    """Modelo para los detalles de una compra (productos comprados)"""
    
    id_detalle = models.BigAutoField(primary_key=True)
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "detalle_compra"
        verbose_name = 'Detalle de Compra'
        verbose_name_plural = 'Detalles de Compra'

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

    def save(self, *args, **kwargs):
        from decimal import Decimal
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        self.compra.total = Decimal(str(self.compra.total)) + Decimal(str(self.subtotal))
        self.compra.save(update_fields=['total'])
        
    def actualizar_stock(self):
        """Actualiza el stock del producto sumándole la cantidad comprada"""
        self.producto.stock_actual += self.cantidad
        self.producto.save()