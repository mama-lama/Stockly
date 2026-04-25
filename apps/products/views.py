from pathlib import Path
import csv
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone

MENU = [
    {'title': 'Главная', 'url': '/'},
    {'title': 'Товары', 'url': '/products/'},
    {'title': 'Прогноз', 'url': '/forecast/'},
    {'title': 'Поставщики', 'url': '/suppliers/'},
    {'title': 'Заявка', 'url': '/application/'},
    {'title': 'Импорт', 'url': '/imports/'},
]

DATA_FILE = settings.BASE_DIR / 'sample_data.csv'


def to_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def save_uploaded_file(uploaded_file):
    with open(DATA_FILE, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)


def load_products():
    if not Path(DATA_FILE).exists():
        return []

    products_map = {}

    with open(DATA_FILE, mode='r', encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)

        for row in reader:
            name = (row.get('name') or '').strip()
            category = (row.get('category') or '').strip()
            supplier = (row.get('supplier') or '').strip()

            if not name:
                continue

            key = name.lower()

            products_map[key] = {
                'id': len(products_map) + 1,
                'name': name,
                'category': category,
                'supplier': supplier,
                'purchase_price': to_int(row.get('purchase_price')),
                'sale_price': to_int(row.get('sale_price')),
                'stock_quantity': to_int(row.get('stock_quantity')),
            }

    return list(products_map.values())


def product_list(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('database_file')

        if not uploaded_file:
            messages.error(request, 'Файл не выбран.')
            return redirect('product_list')

        if not uploaded_file.name.lower().endswith('.csv'):
            messages.error(request, 'Загрузите CSV-файл.')
            return redirect('product_list')

        save_uploaded_file(uploaded_file)
        messages.success(request, 'База успешно загружена.')
        return redirect('product_list')

    query = request.GET.get('q', '').strip().lower()
    selected_category = request.GET.get('category', '').strip()
    selected_supplier = request.GET.get('supplier', '').strip()

    all_products = load_products()

    categories = sorted({
        product['category']
        for product in all_products
        if product.get('category')
    })

    suppliers = sorted({
        product['supplier']
        for product in all_products
        if product.get('supplier')
    })

    products = all_products

    if query:
        products = [
            product for product in products
            if query in product['name'].lower()
        ]

    if selected_category:
        products = [
            product for product in products
            if product['category'] == selected_category
        ]

    if selected_supplier:
        products = [
            product for product in products
            if product['supplier'] == selected_supplier
        ]

    context = {
        'title': 'Список товаров',
        'headers': ['Название', 'Категория', 'Цена продажи','Закупочная цена', 'Остаток', 'Поставщик'],
        'products': products,
        'query': request.GET.get('q', '').strip(),
        'menu': MENU,
        'categories': categories,
        'suppliers': suppliers,
        'selected_category': selected_category,
        'selected_supplier': selected_supplier,
    }

    return render(request, 'products/product_list.html', context)


def product_detail(request, product_id):
    all_products = load_products()
    product = next((item for item in all_products if item['id'] == product_id), None)

    context = {
        'title': 'Карточка товара',
        'product': product,
        'menu': MENU,
    }

from datetime import timedelta
from django.shortcuts import render
from django.utils import timezone


def product_detail(request, product_id):
    all_products = load_products()
    product = next((item for item in all_products if str(item['id']) == str(product_id)), None)

    today = timezone.localdate()

    sales_data = [5, 8, 3, 10, 7, 12, 6, 4, 9, 11, 5, 8, 6, 7, 13, 9, 4, 3, 6, 8, 10, 7, 5, 9, 12, 11, 6, 4, 8, 10]

    daily_series = []
    for i in range(30):
        day = today - timedelta(days=29 - i)
        daily_series.append({
            'date': day.strftime('%d.%m'),
            'sales': sales_data[i],
        })

    max_sales = max((item['sales'] for item in daily_series), default=1)

    for item in daily_series:
        item['width'] = round((item['sales'] / max_sales) * 100, 1) if max_sales else 0

    context = {
        'title': 'Карточка товара',
        'product': product,
        'menu': MENU,
        'forecast': {
            'daily_series': daily_series,
            'max_sales': max_sales,
        }
    }

    return render(request, 'products/product_card.html', context)