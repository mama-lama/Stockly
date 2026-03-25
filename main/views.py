from django.shortcuts import render

def index(request):
    context = {
        'title': 'Stockly',
        'subtitle': 'Система прогнозирования спроса для розничного магазина',
        'menu': [
            {'title': 'Главная', 'url': '/'},
            {'title': 'Товары', 'url': '/products/'},
            {'title': 'Прогноз', 'url': 'forecast'},
            {'title': 'Поставщики', 'url': 'suppliers'},
        
        ]
    }

    return render(request, 'main/index.html', context)