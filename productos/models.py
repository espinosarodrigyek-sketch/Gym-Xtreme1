from django.db import models


class Categoria(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    es_consumible = models.BooleanField(default=False)

    class Meta:
        db_table = 'categorias'

    def __str__(self):
        return self.nombre


class Producto(models.Model):

    id_producto = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=100)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos',
        db_column='categoria_id',
    )
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Precio de compra al proveedor")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.IntegerField()

    tiene_maquina = models.BooleanField(default=False)
    maquina_id = models.IntegerField(null=True, blank=True)

    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo')
    ]

    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)

    class Meta:
        db_table = 'productos'

    def __init__(self, *args, **kwargs):
        categoria = kwargs.pop('categoria', None)
        if isinstance(categoria, str):
            categoria_nombre = categoria.strip()
            if categoria_nombre:
                categoria_obj, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
                kwargs['categoria'] = categoria_obj
            else:
                kwargs['categoria'] = None
        super().__init__(*args, **kwargs)

    def get_proveedores(self):
        """Obtiene los proveedores relacionados a través de las compras"""
        from proveedores.models import Proveedor
        return Proveedor.objects.filter(
            compras__detalles__producto=self
        ).distinct()

    def save(self, *args, **kwargs):
        if isinstance(self.categoria, str):
            categoria_nombre = self.categoria.strip()
            if categoria_nombre:
                categoria_obj, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
                self.categoria = categoria_obj
            else:
                self.categoria = None
        super().save(*args, **kwargs)

    def margen_ganancia(self):
        if self.precio_costo and self.precio_costo > 0:
            return float(self.precio_venta) - float(self.precio_costo)
        return 0

    def porcentaje_margen(self):
        if self.precio_costo and self.precio_costo > 0:
            return round(((float(self.precio_venta) - float(self.precio_costo)) / float(self.precio_costo)) * 100, 1)
        return 0

    def __str__(self):
        return self.nombre