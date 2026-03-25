from django.shortcuts import render


def suppliers_page(request):
    context = {
        'title': 'Поставщики',
        'menu': [
            {'title': 'Главная', 'url': '/'},
            {'title': 'Товары', 'url': '/products/'},
            {'title': 'Прогноз', 'url': '/forecast/'},
            {'title': 'Поставщики', 'url': '/suppliers/'},
        ]
    }
    return render(request, 'suppliers/suppliers.html', context)