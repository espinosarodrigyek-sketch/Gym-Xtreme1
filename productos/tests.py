from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from decimal import Decimal
from productos.models import Producto, Categoria
from productos.views import catalogo


class CatalogoViewTest(TestCase):
    def test_catalogo_view_renderiza_sin_error(self):
        Categoria.objects.get_or_create(nombre='Suplementos')
        Producto.objects.create(
            nombre='Proteína Whey',
            descripcion='Proteína en polvo',
            categoria='Suplementos',
            precio_costo=Decimal('50000'),
            precio_venta=Decimal('80000'),
            stock_actual=10,
            estado='activo'
        )

        factory = RequestFactory()
        request = factory.get('/productos/tienda/')
        response = catalogo(request)

        self.assertEqual(response.status_code, 200)


class ProductoModelTest(TestCase):
    """Tests para el modelo Producto"""
    
    def test_crear_producto(self):
        """Test crear producto"""
        Categoria.objects.get_or_create(nombre='Suplementos')
        producto = Producto.objects.create(
            nombre='Proteína Whey',
            descripcion='Proteína en polvo',
            categoria='Suplementos',
            precio_costo=Decimal('50000'),
            precio_venta=Decimal('80000'),
            stock_actual=10,
            estado='activo'
        )
        
        self.assertEqual(producto.nombre, 'Proteína Whey')
        self.assertEqual(producto.estado, 'activo')
    
    def test_margen_ganancia(self):
        """Test cálculo de margen de ganancia"""
        Categoria.objects.get_or_create(nombre='Suplementos')
        producto = Producto.objects.create(
            nombre='Creatina',
            descripcion='Creatina monohidratada',
            categoria='Suplementos',
            precio_costo=Decimal('30000'),
            precio_venta=Decimal('50000'),
            stock_actual=20,
            estado='activo'
        )
        
        margen = producto.margen_ganancia()
        self.assertEqual(margen, 20000)
    
    def test_porcentaje_margen(self):
        """Test cálculo de porcentaje de margen"""
        Categoria.objects.get_or_create(nombre='Suplementos')
        producto = Producto.objects.create(
            nombre='Pre-workout',
            descripcion='Pre entrenamiento',
            categoria='Suplementos',
            precio_costo=Decimal('40000'),
            precio_venta=Decimal('60000'),
            stock_actual=15,
            estado='activo'
        )
        
        porcentaje = producto.porcentaje_margen()
        self.assertEqual(porcentaje, 50.0)
    
    def test_producto_inactivo(self):
        """Test producto con estado inactivo"""
        Categoria.objects.get_or_create(nombre='Varios')
        producto = Producto.objects.create(
            nombre='Producto obsolete',
            descripcion='Producto discontinued',
            categoria='Varios',
            precio_costo=Decimal('10000'),
            precio_venta=Decimal('20000'),
            stock_actual=0,
            estado='inactivo'
        )
        
        self.assertEqual(producto.estado, 'inactivo')
        self.assertEqual(producto.stock_actual, 0)


class CarritoTest(TestCase):
    """Tests para el carrito de compras"""
    
    def test_calculo_total_carrito(self):
        """Test cálculo de total en carrito"""
        # Simular estructura del carrito en sesión
        carrito = {
            '1': {'nombre': 'Producto 1', 'precio': '10000', 'cantidad': 2},
            '2': {'nombre': 'Producto 2', 'precio': '20000', 'cantidad': 1},
        }
        
        total = sum(
            int(item['cantidad']) * float(item['precio']) 
            for item in carrito.values()
        )
        
        self.assertEqual(total, 40000)  # (2*10000) + (1*20000)
