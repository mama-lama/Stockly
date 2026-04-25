from django.shortcuts import render

def forecast_page(request):
    context = {
        'title': 'Прогноз',
        'menu': [
            {'title': 'Главная', 'url': '/'},
            {'title': 'Товары', 'url': '/products/'},
            {'title': 'Прогноз', 'url': '/forecast/'},
            {'title': 'Поставщики', 'url': '/suppliers/'},
            {'title': 'Заявка', 'url': '/application/'},
            {'title': 'Импорт', 'url': '/imports/'},
        ]
    }
    return render(request, 'forecasting/forecast.html', context)