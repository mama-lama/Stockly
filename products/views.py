from django.shortcuts import render

MENU = [
    {'title': 'Главная', 'url': '/'},
    {'title': 'Товары', 'url': '/products/'},
    {'title': 'Прогноз', 'url': '/forecast/'},
    {'title': 'Поставщики', 'url': '/suppliers/'},
]

ALL_PRODUCTS = [
    {
        'id': 1,
        'name': 'Молоко 2.5%',
        'category': 'Молочная продукция',
        'sale_price': 89,
        'stock_quantity': 24,
        'supplier': 'ООО МолТорг',
    },
    {
        'id': 2,
        'name': 'Хлеб пшеничный',
        'category': 'Хлебобулочные изделия',
        'sale_price': 45,
        'stock_quantity': 17,
        'supplier': 'Хлебозавод №1',
    },
    {
        'id': 3,
        'name': 'Кофе молотый 250 г',
        'category': 'Бакалея',
        'sale_price': 329,
        'stock_quantity': 8,
        'supplier': 'Coffee Trade',
    },
]


def product_list(request):
    query = request.GET.get('q', '').strip()

    if query:
        products = [
            product for product in ALL_PRODUCTS
            if query.lower() in product['name'].lower()
        ]
    else:
        products = ALL_PRODUCTS

    context = {
        'title': 'Список товаров',
        'headers': ['Название', 'Категория', 'Цена продажи', 'Остаток', 'Поставщик'],
        'products': products,
        'query': query,
        'menu': MENU,
    }

    return render(request, 'products/product_list.html', context)


def product_detail(request, product_id):
    product = next(
        (item for item in ALL_PRODUCTS if item['id'] == product_id),
        None
    )

    context = {
        'title': 'Карточка товара',
        'product': product,
        'menu': MENU,
    }

    return render(request, 'products/product_card.html', context)