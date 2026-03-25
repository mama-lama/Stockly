from django.shortcuts import render

def product_list(request):
    all_products = [
        {
            'name': 'Молоко 2.5%',
            'category': 'Молочная продукция',
            'sale_price': 89,
            'stock_quantity': 24,
            'supplier': 'ООО МолТорг',
        },
        {
            'name': 'Хлеб пшеничный',
            'category': 'Хлебобулочные изделия',
            'sale_price': 45,
            'stock_quantity': 17,
            'supplier': 'Хлебозавод №1',
        },
        {
            'name': 'Кофе молотый 250 г',
            'category': 'Бакалея',
            'sale_price': 329,
            'stock_quantity': 8,
            'supplier': 'Coffee Trade',
        },
    ]

    query = request.GET.get('q', '').strip()

    if query:
        products = [
            product for product in all_products
            if query.lower() in product['name'].lower()
        ]
    else:
        products = all_products

    context = {
        'title': 'Список товаров',
        'headers': ['Название', 'Категория', 'Цена продажи', 'Остаток', 'Поставщик'],
        'products': products,
        'query': query,
        'menu': [
            {'title': 'Главная', 'url': '/'},
            {'title': 'Товары', 'url': '/products/'},
            {'title': 'Прогноз', 'url': '/forecast/'},
            {'title': 'Поставщики', 'url': '/suppliers/'},
        ]
    }

    return render(request, 'products/product_list.html', context)

