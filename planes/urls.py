from django.urls import path, include

app_name = 'planes'

urlpatterns = [
    path('', include('usuarios.urls', namespace='usuarios')),  # Alias to ver_planes
]
