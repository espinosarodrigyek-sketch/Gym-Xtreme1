"""
API de rutinas desde CSV/Database.
"""
import logging
import csv
import os
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from usuarios.models import Rutina, Ejercicio

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def api_rutinas(request):
    """
    API que retorna las rutinas del sistema.
    Primero intenta leer de la base de datos, si no hay usa el CSV.
    """
    try:
        rutinas_db = Rutina.objects.filter(
            activa=True, 
            es_predeterminada=True
        ).prefetch_related('ejercicios')
        
        if rutinas_db.exists():
            rutinas_data = []
            for rutina in rutinas_db:
                ejercicios = []
                for ej in rutina.ejercicios.all().order_by('dia', 'orden'):
                    ejercicios.append({
                        'nombre': ej.nombre,
                        'series': ej.series,
                        'repeticiones': ej.repeticiones,
                        'descanso': ej.descanso,
                        'dia': ej.dia
                    })
                
                rutinas_data.append({
                    'id': rutina.id,
                    'nombre': rutina.nombre,
                    'nivel': rutina.nivel,
                    'duracion_dias': rutina.duracion_dias,
                    'ejercicios': ejercicios
                })
            
            return JsonResponse({
                'success': True,
                'fuente': 'database',
                'rutinas': rutinas_data,
                'total': len(rutinas_data)
            })
        
        return api_rutinas_csv(request)
        
    except Exception as e:
        logger.error(f"Error cargando rutinas de DB: {e}")
        return api_rutinas_csv(request)


def api_rutinas_csv(request):
    """
    Carga rutinas desde el archivo CSV como fallback.
    """
    csv_path = os.path.join('gym', 'csv_datos', 'rutinas.csv')
    
    if not os.path.exists(csv_path):
        return JsonResponse({
            'success': False,
            'error': 'No hay rutinas disponibles'
        }, status=404)
    
    try:
        rutinas_dict = {}
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rutina_num = row.get('rutina', '1')
                dia = row.get('dia', 'lunes').lower()
                
                if rutina_num not in rutinas_dict:
                    rutinas_dict[rutina_num] = {
                        'nombre': f'Rutina {rutina_num}',
                        'ejercicios': []
                    }
                
                ejercicios = row.get('ejercicios', '').split(',')
                for i, ej_nombre in enumerate(ejercicios):
                    if ej_nombre.strip():
                        rutinas_dict[rutina_num]['ejercicios'].append({
                            'nombre': ej_nombre.strip(),
                            'series': int(row.get('series', 4)),
                            'repeticiones': row.get('repeticiones', '10-12').strip(),
                            'descanso': int(row.get('descanso', 90)),
                            'dia': dia
                        })
        
        return JsonResponse({
            'success': True,
            'fuente': 'csv',
            'rutinas': list(rutinas_dict.values()),
            'total': len(rutinas_dict)
        })
        
    except Exception as e:
        logger.error(f"Error leyendo CSV de rutinas: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_frases(request):
    """
    API visible en navegador para frases motivacionales.
    """
    from .frases import obtener_frase_motivacional
    
    frase = obtener_frase_motivacional()
    return JsonResponse({
        'success': True,
        'frase': frase['frase'],
        'autor': frase['autor'],
        'fuente': 'API Externa (ZenQuotes)',
        'traduccion': 'MyMemory API'
    })