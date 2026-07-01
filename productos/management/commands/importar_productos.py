import os
import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from productos.models import Producto
from proveedores.models import Proveedor


class Command(BaseCommand):
    help = 'Importa productos desde CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default='csv_datos/productos.csv',
            help='Ruta al archivo CSV de productos'
        )
        parser.add_argument(
            '--proveedores',
            type=str,
            default='csv_datos/proveedores_productos.csv',
            help='Ruta al archivo CSV de proveedores-productos'
        )
        parser.add_argument(
            '--actualizar',
            action='store_true',
            help='Actualizar productos existentes'
        )
        parser.add_argument(
            '--limite',
            type=int,
            default=None,
            help='Limite de productos a importar'
        )

    def handle(self, *args, **options):
        self.csv_path = options.get('csv')
        self.proveedores_path = options.get('proveedores')
        self.actualizar = options.get('actualizar')
        self.limite = options.get('limite')
        
        self.stats = {
            'creados': 0,
            'actualizados': 0,
            'errores': 0,
            'relaciones': 0
        }
        
        self.stdout.write('='*50)
        self.stdout.write('IMPORTACION DE PRODUCTOS')
        self.stdout.write('='*50)
        
        self.proveedores_mapping = self._cargar_proveedores_productos()
        self._importar_productos()
        self._mostrar_estadisticas()

    def _validar_producto(self, row):
        errores = []
        
        nombre = row.get('nombre', '').strip()
        if not nombre:
            errores.append('Nombre requerido')
        
        try:
            float(row.get('precio_costo', 0))
        except:
            errores.append('precio_costo debe ser numerico')
        
        try:
            float(row.get('precio_venta', 0))
        except:
            errores.append('precio_venta debe ser numerico')
        
        try:
            int(row.get('stock_actual', 0))
        except:
            errores.append('stock_actual debe ser numerico')
        
        estado = row.get('estado', 'activo').strip().lower()
        if estado not in ['activo', 'inactivo']:
            errores.append('estado debe ser activo o inactivo')
        
        return errores

    def _cargar_proveedores_productos(self):
        mapping = {}
        
        if not os.path.exists(self.proveedores_path):
            return mapping
        
        try:
            with open(self.proveedores_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    proveedor_nombre = row.get('proveedor', '').strip()
                    producto_nombre = row.get('producto', '').strip()
                    
                    if proveedor_nombre and producto_nombre:
                        if producto_nombre not in mapping:
                            mapping[producto_nombre] = []
                        mapping[producto_nombre].append(proveedor_nombre)
        except Exception as e:
            self.stdout.write(f'Advertencia: {e}')
        
        return mapping

    def _importar_productos(self):
        if not os.path.exists(self.csv_path):
            self.stdout.write(f'Archivo no encontrado: {self.csv_path}')
            return
        
        contador = 0
        
        with open(self.csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                if self.limite and contador >= self.limite:
                    break
                
                contador += 1
                nombre = row.get('nombre', '').strip()
                
                errores = self._validar_producto(row)
                if errores:
                    self.stdout.write(f'Error en {nombre}: {", ".join(errores)}')
                    self.stats['errores'] += 1
                    continue
                
                try:
                    producto_existente = Producto.objects.filter(nombre__iexact=nombre).first()
                    
                    if producto_existente:
                        if not self.actualizar:
                            self.stdout.write(f'Saltando {nombre} (ya existe, use --actualizar)')
                            continue
                        
                        self._actualizar_producto(producto_existente, row)
                        self.stats['actualizados'] += 1
                    else:
                        self._crear_producto(row)
                        self.stats['creados'] += 1
                    
                except Exception as e:
                    self.stdout.write(f'Error con {nombre}: {str(e)}')
                    self.stats['errores'] += 1

    def _crear_producto(self, row):
        nombre = row.get('nombre', '').strip()
        
        producto = Producto(
            nombre=nombre,
            descripcion=row.get('descripcion', '').strip(),
            categoria=row.get('categoria', '').strip(),
            precio_costo=float(row.get('precio_costo', 0)),
            precio_venta=float(row.get('precio_venta', 0)),
            stock_actual=int(row.get('stock_actual', 0)),
            estado=row.get('estado', 'activo').strip().lower()
        )
        producto.save()
        
        self.stdout.write(f'Creado: {nombre}')
        
        self._relacionar_proveedores(producto)

    def _actualizar_producto(self, producto, row):
        producto.descripcion = row.get('descripcion', '').strip()
        producto.categoria = row.get('categoria', '').strip()
        producto.precio_costo = float(row.get('precio_costo', 0))
        producto.precio_venta = float(row.get('precio_venta', 0))
        producto.stock_actual = int(row.get('stock_actual', 0))
        producto.estado = row.get('estado', 'activo').strip().lower()
        producto.save()
        
        self.stdout.write(f'Actualizado: {producto.nombre}')
        
        self._relacionar_proveedores(producto)

    def _relacionar_proveedores(self, producto):
        nombres_producto = producto.nombre
        
        if nombres_producto in self.proveedores_mapping:
            proveedores_nombres = self.proveedores_mapping[nombres_producto]
            
            for prov_nombre in proveedores_nombres:
                proveedor = Proveedor.objects.filter(nombre__iexact=prov_nombre).first()
                if proveedor:
                    proveedor.productos.add(producto)
                    self.stats['relaciones'] += 1
                    self.stdout.write(f'  Relacionado con: {proveedor.nombre}')

    def _mostrar_estadisticas(self):
        self.stdout.write('='*50)
        self.stdout.write('ESTADISTICAS')
        self.stdout.write('='*50)
        self.stdout.write(f'Productos creados: {self.stats["creados"]}')
        self.stdout.write(f'Productos actualizados: {self.stats["actualizados"]}')
        self.stdout.write(f'Relaciones creadas: {self.stats["relaciones"]}')
        self.stdout.write(f'Errores: {self.stats["errores"]}')
