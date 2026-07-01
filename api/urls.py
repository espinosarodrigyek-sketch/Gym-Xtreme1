from django.urls import path
from . import views
from .frases import frase_api_view
from .rutinas import api_rutinas, api_frases

app_name = 'api'

urlpatterns = [
    path('', views.ejercicios_index, name='ejercicios_index'),
    path('buscar/', views.ejercicios_index, name='buscar_ejercicios'),
    path('categoria/<int:categoria_id>/', views.ejercicios_por_categoria, name='ejercicios_categoria'),
    path('detalle/<str:ejercicio_id>/', views.detalle_ejercicio, name='detalle_ejercicio'),
    path('frase/', views.frase_motivacional, name='frase_motivacional'),
    path('frases/', frase_api_view, name='frase_api_view'),
    path('frases/nueva/', api_frases, name='api_frases'),  # Nueva API visible
    path('rutinas/', api_rutinas, name='api_rutinas'),
    path('productos/proveedor/<int:proveedor_id>/', views.productos_por_proveedor, name='productos_por_proveedor'),
    
    # API AJAX JSON
    path('ajax/buscar-ejercicios/', views.api_buscar_ejercicios, name='ajax_buscar_ejercicios'),
    path('ajax/ejercicios-por-categoria/', views.api_ejercicios_por_categoria, name='ajax_ejercicios_por_categoria'),
    path('ajax/obtener-ejercicio/', views.api_obtener_ejercicio, name='ajax_obtener_ejercicio'),
    path('ajax/obtener-categorias/', views.api_obtener_categorias, name='ajax_obtener_categorias'),
    path('ajax/ejercicios-random/', views.api_ejercicios_random, name='ajax_ejercicios_random'),
]