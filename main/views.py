from django.shortcuts import render

MENU = [
    {'title': 'Главная', 'url': '/'},
    {'title': 'Товары', 'url': '/products/'},
    {'title': 'Прогноз', 'url': '/forecast/'},
    {'title': 'Поставщики', 'url': '/suppliers/'},
    {'title': 'Заявка', 'url': '/application/'},
]

def index(request):
    context = {
        'title': 'Stockly',
        'subtitle': 'Система прогнозирования спроса для розничного магазина',
        'menu': MENU,
    }

    return render(request, 'main/index.html', context)