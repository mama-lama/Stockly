from django.shortcuts import render
from products.views import load_products
MENU = [
    {'title': 'Главная', 'url': '/'},
    {'title': 'Товары', 'url': '/products/'},
    {'title': 'Прогноз', 'url': '/forecast/'},
    {'title': 'Поставщики', 'url': '/suppliers/'},
    {'title': 'Заявка', 'url': '/application/'},
]

def index(request):
    all_products = load_products()
    total_products = len(all_products)
    context = {
        'title': 'Stockly',
        'subtitle': 'Система прогнозирования спроса для розничного магазина',
        'menu': MENU,
        'total_products': total_products,
    }

    return render(request, 'main/index.html', context)