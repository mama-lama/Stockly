from pathlib import Path
from django.conf import settings
from django.shortcuts import render
from django.http import FileResponse, Http404


def application_page(request):
    menu = [
    {'title': 'Главная', 'url': '/'},
    {'title': 'Товары', 'url': '/products/'},
    {'title': 'Прогноз', 'url': '/forecast/'},
    {'title': 'Поставщики', 'url': '/suppliers/'},
    {'title': 'Заявка', 'url': '/application/'},
    {'title': 'Импорт', 'url': '/imports/'},
    ]

    context = {
        'menu': menu
    }

    return render(request, 'application/application.html', context)


def export_excel(request):
    file_path = Path(settings.BASE_DIR) / 'apps' / 'application' / 'files' / 'purchase_order.xlsx'

    if not file_path.exists():
        raise Http404('Файл Excel не найден')

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename='purchase_order.xlsx'
    )