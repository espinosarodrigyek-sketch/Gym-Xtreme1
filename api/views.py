import logging
logger = logging.getLogger(__name__)

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .services import WgerService
from .frases import obtener_frase_motivacional
from proveedores.models import Proveedor
from productos.models import Producto


@require_http_methods(["GET"])
def api_buscar_ejercicios(request):
    """
    API AJAX: Busca ejercicios desde la API externa (Wger)
    Retorna JSON con lista de ejercicios encontrados
    """
    termino = request.GET.get('q', '').strip()
    limite = int(request.GET.get('limit', 20))
    
    logger.info(f"API search request: termino='{termino}', limite={limite}")
    
    if not termino:
        return JsonResponse({'success': False, 'error': 'Se requiere un término de búsqueda'}, status=400)
    
    try:
        resultado = WgerService.buscar_ejercicios(termino, limite=limite)
        
        logger.info(f"API search result: {resultado}")
        
        if 'error' in resultado:
            return JsonResponse({'success': False, 'error': resultado.get('error')}, status=500)
        
        return JsonResponse({
            'success': True,
            'count': resultado.get('count', 0),
            'ejercicios': resultado.get('ejercicios', [])
        })
    except Exception as e:
        logger.error(f"API search error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_ejercicios_por_categoria(request):
    """
    API AJAX: Obtiene ejercicios por categoría
    """
    categoria_id = request.GET.get('categoria_id')
    limite = int(request.GET.get('limit', 20))
    
    if not categoria_id:
        return JsonResponse({'success': False, 'error': 'Se requiere ID de categoría'}, status=400)
    
    try:
        resultado = WgerService.obtener_ejercicios_por_categoria(int(categoria_id), limite=limite)
        
        if 'error' in resultado:
            return JsonResponse({'success': False, 'error': resultado.get('error')}, status=500)
        
        return JsonResponse({
            'success': True,
            'count': resultado.get('count', 0),
            'ejercicios': resultado.get('ejercicios', [])
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_obtener_ejercicio(request):
    """
    API AJAX: Obtiene un ejercicio específico por ID
    """
    ejercicio_id = request.GET.get('id', '')
    
    if not ejercicio_id:
        return JsonResponse({'success': False, 'error': 'Se requiere ID de ejercicio'}, status=400)
    
    try:
        ejercicio = WgerService.obtener_ejercicio_por_id(ejercicio_id)
        
        if not ejercicio:
            return JsonResponse({'success': False, 'error': 'Ejercicio no encontrado'}, status=404)
        
        return JsonResponse({'success': True, 'ejercicio': ejercicio})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_obtener_categorias(request):
    """
    API AJAX: Obtiene todas las categorías de ejercicios
    """
    try:
        resultado = WgerService.obtener_categorias()
        return JsonResponse({
            'success': True,
            'categorias': resultado.get('categorias', [])
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_ejercicios_random(request):
    """
    API AJAX: Obtiene ejercicios aleatorios o recientes
    """
    limite = int(request.GET.get('limit', 12))
    
    try:
        resultado = WgerService.obtener_ejercicios(limite=limite)
        
        if 'error' in resultado:
            return JsonResponse({'success': False, 'error': resultado.get('error')}, status=500)
        
        return JsonResponse({
            'success': True,
            'count': resultado.get('count', 0),
            'ejercicios': resultado.get('ejercicios', [])
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def ejercicios_index(request):
    """Página principal de ejercicios - buscador y exploración"""
    if request.method == 'POST':
        termino = request.POST.get('termino', '').strip()
    else:
        termino = request.GET.get('termino', '').strip()

    ejercicios = []
    total_encontrados = 0
    error = None
    categorias = []

    if termino:
        resultado = WgerService.buscar_ejercicios(termino, limite=20)
        
        if 'error' in resultado:
            error = resultado['error']
        else:
            ejercicios = resultado.get('ejercicios', [])
            total_encontrados = resultado.get('count', 0)
    else:
        resultado_cat = WgerService.obtener_categorias()
        categorias = resultado_cat.get('categorias', [])[:6]
        
        if not categorias:
            resultado_ej = WgerService.obtener_ejercicios(limite=12)
            if 'error' not in resultado_ej:
                ejercicios = resultado_ej.get('ejercicios', [])
                total_encontrados = resultado_ej.get('count', 0)

    return render(request, 'api/ejercicios_index.html', {
        'termino_busqueda': termino,
        'ejercicios': ejercicios,
        'total_encontrados': total_encontrados,
        'categorias': categorias,
        'hay_busqueda': bool(termino),
        'error': error,
    })


def ejercicios_por_categoria(request, categoria_id):
    """Página de ejercicios por categoría"""
    resultado = WgerService.obtener_ejercicios_por_categoria(categoria_id, limite=20)
    
    categoria_nombre = 'Categoría'
    for cat in WgerService.obtener_categorias().get('categorias', []):
        if cat.get('id') == categoria_id:
            categoria_nombre = cat.get('name', 'Categoría')
            break
    
    return render(request, 'api/ejercicios_categoria.html', {
        'ejercicios': resultado.get('ejercicios', []),
        'total_encontrados': resultado.get('count', 0),
        'categoria_id': categoria_id,
        'categoria_nombre': categoria_nombre,
        'error': resultado.get('error'),
    })


def detalle_ejercicio(request, ejercicio_id):
    """Página de detalle de un ejercicio"""
    ejercicio_id_str = str(ejercicio_id)
    ejercicio = WgerService.obtener_ejercicio_por_id(ejercicio_id_str)

    if not ejercicio:
        return render(request, 'api/ejercicios_index.html', {
            'error': 'Ejercicio no encontrado'
        })

    return render(request, 'api/detalle_ejercicio.html', {
        'ejercicio': ejercicio
    })


def frase_motivacional(request):
    """API para obtener una frase motivacional aleatoria"""
    frase = obtener_frase_motivacional()
    return JsonResponse(frase)


def productos_por_proveedor(request, proveedor_id):
    """API AJAX: retorna los productos asociados a un proveedor"""
    try:
        proveedor = Proveedor.objects.get(id_proveedor=proveedor_id)
        productos = proveedor.productos.all()
        
        productos_data = [
            {
                'id': p.id_producto,
                'nombre': p.nombre,
                'stock': p.stock_actual,
                'precio_costo': float(p.precio_costo) if p.precio_costo else 0,
                'precio_venta': float(p.precio_venta) if p.precio_venta else 0,
            }
            for p in productos
        ]
        
        return JsonResponse({
            'success': True,
            'productos': productos_data
        })
    except Proveedor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Proveedor no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)