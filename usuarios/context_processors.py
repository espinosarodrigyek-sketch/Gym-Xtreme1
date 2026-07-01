def user_context(request):
    """Hace disponible el usuario en todos los templates"""
    if hasattr(request, 'user') and request.user.is_authenticated:
        return {
            'is_superuser': request.user.is_superuser,
            'is_staff': request.user.is_staff,
        }
    return {
        'is_superuser': False,
        'is_staff': False,
    }
