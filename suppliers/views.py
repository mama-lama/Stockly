from django.shortcuts import render
from products.views import load_products, MENU


def suppliers_list(request):
    all_products = load_products()

    suppliers_map = {}

    for product in all_products:
        supplier_name = product.get('supplier', '').strip()
        if not supplier_name:
            continue

        if supplier_name not in suppliers_map:
            suppliers_map[supplier_name] = {
                'name': supplier_name,
                'products_count': 0,
            }

        suppliers_map[supplier_name]['products_count'] += 1

    suppliers = sorted(suppliers_map.values(), key=lambda item: item['name'])

    context = {
        'title': 'Поставщики',
        'suppliers': suppliers,
        'menu': MENU,
    }

    return render(request, 'suppliers/suppliers.html', context)