def carrito_total(request):
    if not hasattr(request, 'session'):
        return {'carrito_total': 0}

    carrito = request.session.get('carrito', {})
    total = sum(item['cantidad'] for item in carrito.values())
    return {'carrito_total': total}