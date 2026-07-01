import csv
import os
from datetime import datetime
from django.contrib.auth.models import User
from usuarios.models import Perfil, Suscripcion, HistorialPeso, MetaUsuario
from productos.models import Producto
from planes.models import Plan
from proveedores.models import Proveedor, Devolucion
from maquinaria.models import Maquinaria
from compras.models import Compra, DetalleCompra
from ventas.models import Venta as VentaProducto, DetalleVenta
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal


def importar_usuarios_desde_csv(file_path):
    """Importa usuarios/clientes desde CSV"""
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row.get('username', '').strip()
            email = row.get('email', '').strip()
            password = row.get('password', 'password123')
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            rol = row.get('rol', 'cliente').strip()
            telefono = row.get('telefono', '').strip()
            direccion = row.get('direccion', '').strip()
            edad = row.get('edad', '').strip()
            peso = row.get('peso', '').strip()
            estatura = row.get('estatura', '').strip()
            
            if not username:
                continue
                
            if User.objects.filter(username=username).exists():
                continue
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            perfil = Perfil.objects.create(
                user=user,
                rol=rol,
                telefono=telefono,
                direccion=direccion,
                edad=int(edad) if edad else None,
                peso=Decimal(peso) if peso else None,
                estatura=Decimal(estatura) if estatura else None
            )
            cantidad += 1
            
    return cantidad


def importar_productos_desde_csv(file_path):
    """Importa productos desde CSV"""
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nombre = row.get('nombre', '').strip()
            descripcion = row.get('descripcion', '').strip()
            categoria = row.get('categoria', '').strip()
            precio_costo = row.get('precio_costo', '0')
            precio_venta = row.get('precio_venta', '0')
            stock_actual = row.get('stock_actual', '0')
            estado = row.get('estado', 'activo').strip()
            imagen_nombre = row.get('imagen', '').strip()
            
            if not nombre:
                continue
            
            if Producto.objects.filter(nombre=nombre).exists():
                continue
            
            producto = Producto(
                nombre=nombre,
                descripcion=descripcion,
                categoria=categoria,
                precio_costo=precio_costo,
                precio_venta=precio_venta,
                stock_actual=int(stock_actual),
                estado=estado
            )
            if imagen_nombre:
                producto.imagen = 'productos/' + imagen_nombre
            producto.save()
            cantidad += 1
            
    return cantidad


def importar_planes_desde_csv(file_path):
    """Importa planes desde CSV"""
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nombre = row.get('nombre', '').strip()
            tipo = row.get('tipo', '1_mes').strip()
            precio = row.get('precio', '0')
            descripcion = row.get('descripcion', '').strip()
            duracion_dias = row.get('duracion_dias', '30')
            
            if not nombre:
                continue
            
            if Plan.objects.filter(nombre=nombre).exists():
                continue
            
            plan = Plan(
                nombre=nombre,
                tipo=tipo,
                precio=precio,
                descripcion=descripcion,
                duracion_dias=int(duracion_dias)
            )
            plan.save()
            cantidad += 1
            
    return cantidad


def importar_proveedores_desde_csv(file_path):
    """Importa proveedores desde CSV"""
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nombre = row.get('nombre', '').strip()
            telefono = row.get('telefono', '').strip()
            email = row.get('email', '').strip()
            direccion = row.get('direccion', '').strip()
            ciudad = row.get('ciudad', '').strip()
            contacto = row.get('contacto', '').strip()
            estado = row.get('estado', 'activo').strip()
            
            if not nombre:
                continue
            
            if Proveedor.objects.filter(nombre=nombre).exists():
                continue
            
            proveedor = Proveedor(
                nombre=nombre,
                telefono=telefono,
                email=email,
                direccion=direccion,
                ciudad=ciudad,
                contacto=contacto,
                estado=estado
            )
            proveedor.save()
            cantidad += 1
            
    return cantidad


def importar_maquinaria_desde_csv(file_path):
    """Importa maquinaria desde CSV"""
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nombre = row.get('nombre', '').strip()
            descripcion = row.get('descripcion', '').strip()
            tipo = row.get('tipo', 'otro').strip()
            ubicacion = row.get('ubicacion', '').strip()
            estado = row.get('estado', 'activo').strip()
            precio_compra = row.get('precio_compra', '').strip()
            fecha_compra = row.get('fecha_compra', '').strip()
            proveedor_nombre = row.get('proveedor', '').strip()
            
            if not nombre:
                continue
            
            if Maquinaria.objects.filter(nombre=nombre).exists():
                continue
            
            proveedor = None
            if proveedor_nombre:
                proveedor = Proveedor.objects.filter(nombre=proveedor_nombre).first()
            
            maquinaria = Maquinaria(
                nombre=nombre,
                descripcion=descripcion,
                tipo=tipo,
                ubicacion=ubicacion,
                estado=estado,
                proveedor=proveedor
            )
            
            if precio_compra:
                maquinaria.precio_compra = Decimal(precio_compra)
            
            if fecha_compra:
                try:
                    maquinaria.fecha_compra = datetime.strptime(fecha_compra, '%Y-%m-%d').date()
                except:
                    pass
            
            maquinaria.save()
            cantidad += 1
            
    return cantidad


def importar_compras_desde_csv(file_path):
    """Importa compras a proveedores desde CSV"""
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            proveedor_nombre = row.get('proveedor', '').strip()
            fecha_str = row.get('fecha', '').strip()
            total = row.get('total', '0').strip()
            estado = row.get('estado', 'completada').strip()
            notas = row.get('notas', '').strip()
            productos_data = row.get('productos', '').strip()
            
            if not proveedor_nombre:
                continue
            
            proveedor = Proveedor.objects.filter(nombre=proveedor_nombre).first()
            if not proveedor:
                continue
            
            compra = Compra(
                proveedor=proveedor,
                total=Decimal(total),
                estado=estado,
                notas=notas
            )
            
            if fecha_str:
                try:
                    compra.fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                except:
                    pass
            
            compra.save()
            
            if productos_data:
                productos_list = productos_data.split(';')
                for prod_data in productos_list:
                    if ':' in prod_data:
                        prod_nombre, cantidad_str = prod_data.split(':')
                        producto = Producto.objects.filter(nombre=prod_nombre.strip()).first()
                        if producto:
                            DetalleCompra.objects.create(
                                compra=compra,
                                producto=producto,
                                cantidad=int(cantidad_str.strip()),
                                precio_unitario=producto.precio_costo or 0
                            )
            
            cantidad += 1
            
    return cantidad


def importar_ventas_productos_desde_csv(file_path):
    """Importa ventas de productos desde CSV"""
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row.get('usuario', '').strip()
            fecha_str = row.get('fecha', '').strip()
            total = row.get('total', '0').strip()
            metodo_pago = row.get('metodo_pago', 'efectivo').strip()
            estado = row.get('estado', 'completada').strip()
            productos_data = row.get('productos', '').strip()
            
            if not username:
                continue
            
            user = User.objects.filter(username=username).first()
            if not user:
                continue
            
            venta = VentaProducto(
                usuario=user,
                total=Decimal(total),
                metodo_pago=metodo_pago,
                estado=estado
            )
            
            if fecha_str:
                try:
                    venta.fecha = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
                except:
                    try:
                        venta.fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                    except:
                        pass
            
            venta.save()
            
            if productos_data:
                productos_list = productos_data.split(';')
                for prod_data in productos_list:
                    if ':' in prod_data:
                        parts = prod_data.split(':')
                        prod_nombre = parts[0].strip()
                        cantidad_str = parts[1].strip() if len(parts) > 1 else '1'
                        precio_str = parts[2].strip() if len(parts) > 2 else '0'
                        
                        producto = Producto.objects.filter(nombre=prod_nombre).first()
                        if producto:
                            DetalleVenta.objects.create(
                                venta=venta,
                                producto=producto,
                                cantidad=int(cantidad_str),
                                precio_unitario=Decimal(precio_str) if precio_str else producto.precio_venta,
                                subtotal=Decimal(cantidad_str) * (Decimal(precio_str) if precio_str else producto.precio_venta)
                            )
            
            cantidad += 1
            
    return cantidad


def importar_suscripciones_desde_csv(file_path):
    """Importa suscripciones de clientes desde CSV"""
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row.get('usuario', '').strip()
            plan_nombre = row.get('plan', '').strip()
            fecha_inicio = row.get('fecha_inicio', '').strip()
            fecha_fin = row.get('fecha_fin', '').strip()
            objetivo = row.get('objetivo', 'mantener').strip()
            activa = row.get('activa', 'True').strip().lower() == 'true'
            
            if not username or not plan_nombre:
                continue
            
            user = User.objects.filter(username=username).first()
            if not user:
                continue
            
            plan = Plan.objects.filter(nombre=plan_nombre).first()
            if not plan:
                continue
            
            suscripcion = Suscripcion(
                usuario=user,
                plan=plan,
                objetivo_rutina=objetivo,
                activa=activa
            )
            
            if fecha_inicio:
                try:
                    suscripcion.fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                except:
                    suscripcion.fecha_inicio = timezone.now().date()
            
            if fecha_fin:
                try:
                    suscripcion.fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                except:
                    pass
            
            suscripcion.save()
            cantidad += 1
            
    return cantidad


def importar_historial_peso_desde_csv(file_path):
    """Importa historial de peso desde CSV"""
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row.get('usuario', '').strip()
            peso = row.get('peso', '').strip()
            estatura = row.get('estatura', '').strip()
            rutina = row.get('rutina', '').strip()
            notas = row.get('notas', '').strip()
            fecha_str = row.get('fecha', '').strip()
            
            if not username or not peso:
                continue
            
            user = User.objects.filter(username=username).first()
            if not user:
                continue
            
            registro = HistorialPeso(
                usuario=user,
                peso=Decimal(peso),
                estatura=Decimal(estatura) if estatura else None,
                rutina=rutina,
                notas=notas
            )
            
            if fecha_str:
                try:
                    registro.fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                except:
                    pass
            
            registro.save()
            cantidad += 1
            
    return cantidad


def importar_metas_desde_csv(file_path):
    """Importa metas de usuarios desde CSV"""
    cantidad = 0
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row.get('usuario', '').strip()
            descripcion = row.get('descripcion', '').strip()
            peso_objetivo = row.get('peso_objetivo', '').strip()
            fecha_objetivo = row.get('fecha_objetivo', '').strip()
            tipo = row.get('tipo', 'peso').strip()
            estado = row.get('estado', 'activa').strip()
            
            if not username or not descripcion:
                continue
            
            user = User.objects.filter(username=username).first()
            if not user:
                continue
            
            meta = MetaUsuario(
                usuario=user,
                descripcion=descripcion,
                tipo=tipo,
                estado=estado
            )
            
            if peso_objetivo:
                meta.peso_objetivo = Decimal(peso_objetivo)
            
            if fecha_objetivo:
                try:
                    meta.fecha_objetivo = datetime.strptime(fecha_objetivo, '%Y-%m-%d').date()
                except:
                    pass
            
            meta.save()
            cantidad += 1
            
    return cantidad


def importar_todo_desde_csv(directorio):
    """Importa todos los CSV desde un directorio"""
    resultados = {}
    
    # Mapeo de archivos a funciones
    archivos = {
        'usuarios.csv': importar_usuarios_desde_csv,
        'clientes.csv': importar_usuarios_desde_csv,
        'productos.csv': importar_productos_desde_csv,
        'planes.csv': importar_planes_desde_csv,
        'proveedores.csv': importar_proveedores_desde_csv,
        'maquinaria.csv': importar_maquinaria_desde_csv,
        'compras.csv': importar_compras_desde_csv,
        'ventas_productos.csv': importar_ventas_productos_desde_csv,
        'suscripciones.csv': importar_suscripciones_desde_csv,
        'historial_peso.csv': importar_historial_peso_desde_csv,
        'metas.csv': importar_metas_desde_csv,
    }
    
    for archivo, funcion in archivos.items():
        ruta = os.path.join(directorio, archivo)
        if os.path.exists(ruta):
            try:
                cantidad = funcion(ruta)
                resultados[archivo] = {'exitoso': True, 'cantidad': cantidad}
            except Exception as e:
                resultados[archivo] = {'exitoso': False, 'error': str(e)}
        else:
            resultados[archivo] = {'exitoso': False, 'error': 'Archivo no encontrado'}
    
    return resultados


# Funciones de ayuda para crear CSVs de ejemplo
def crear_csv_ejemplo(tipo, file_path):
    """Crea un CSV de ejemplo según el tipo"""
    import csv
    
    funciones = {
        'usuarios': lambda w: escribir_csv_usuarios(w),
        'productos': lambda w: escribir_csv_productos(w),
        'planes': lambda w: escribir_csv_planes(w),
        'proveedores': lambda w: escribir_csv_proveedores(w),
        'maquinaria': lambda w: escribir_csv_maquinaria(w),
        'compras': lambda w: escribir_csv_compras(w),
        'ventas_productos': lambda w: escribir_csv_ventas_productos(w),
        'suscripciones': lambda w: escribir_csv_suscripciones(w),
    }
    
    if tipo in funciones:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            funciones[tipo](csv.writer(f))
        return True
    return False


def escribir_csv_usuarios(w):
    w.writerow(['username', 'email', 'password', 'first_name', 'last_name', 'rol', 'telefono', 'direccion', 'edad', 'peso', 'estatura'])
    w.writerow(['cliente1', 'cliente1@test.com', 'password123', 'Juan', 'Perez', 'cliente', '3001234567', 'Calle 123', '30', '75', '1.75'])
    w.writerow(['cliente2', 'cliente2@test.com', 'password123', 'Maria', 'Gomez', 'cliente', '3002345678', 'Carrera 456', '25', '60', '1.60'])


def escribir_csv_productos(w):
    w.writerow(['nombre', 'descripcion', 'categoria', 'precio_costo', 'precio_venta', 'stock_actual', 'estado'])
    w.writerow(['Proteína Whey', 'Suplemento de proteína', 'Suplementos', '80000', '120000', '50', 'activo'])
    w.writerow(['Creatina Monohidrato', 'Creatina de alta pureza', 'Suplementos', '45000', '75000', '30', 'activo'])


def escribir_csv_planes(w):
    w.writerow(['nombre', 'tipo', 'precio', 'descripcion', 'duracion_dias'])
    w.writerow(['Plan Básico', '1_mes', '80000', 'Acceso básico al gimnasio', '30'])
    w.writerow(['Plan Premium', '1_mes', '150000', 'Acceso total + clases', '30'])


def escribir_csv_proveedores(w):
    w.writerow(['nombre', 'telefono', 'email', 'direccion', 'ciudad', 'contacto', 'estado'])
    w.writerow(['Distribuidora fitness', '3001112233', 'info@distrifit.com', 'Calle 10 #20-30', 'Bogotá', 'Carlos Martínez', 'activo'])


def escribir_csv_maquinaria(w):
    w.writerow(['nombre', 'descripcion', 'tipo', 'ubicacion', 'estado', 'precio_compra', 'fecha_compra', 'proveedor'])
    w.writerow(['Cinta para correr', 'Cinta profesional', 'cardio', 'Zona cardio', 'activo', '5000000', '2024-01-15', 'Distribuidora fitness'])
    w.writerow(['Mancuernas 10kg', 'Pares de mancuernas', 'fuerza', 'Zona pesas', 'activo', '200000', '2024-02-01', 'Distribuidora fitness'])


def escribir_csv_compras(w):
    w.writerow(['proveedor', 'fecha', 'total', 'estado', 'notas', 'productos'])
    w.writerow(['Distribuidora fitness', '2024-01-20', '3000000', 'completada', 'Compra mensual', 'Proteína Whey:20;Creatina:10'])


def escribir_csv_ventas_productos(w):
    w.writerow(['usuario', 'fecha', 'total', 'metodo_pago', 'estado', 'productos'])
    w.writerow(['cliente1', '2024-03-01 10:30:00', '120000', 'efectivo', 'completada', 'Proteína Whey:1:120000'])


def escribir_csv_suscripciones(w):
    w.writerow(['usuario', 'plan', 'fecha_inicio', 'fecha_fin', 'objetivo', 'activa'])
    w.writerow(['cliente1', 'Plan Básico', '2024-03-01', '2024-04-01', 'mantener', 'True'])