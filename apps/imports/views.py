import csv
import io

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render


MENU = [
    {'title': 'Главная', 'url': '/'},
    {'title': 'Товары', 'url': '/products/'},
    {'title': 'Прогноз', 'url': '/forecast/'},
    {'title': 'Поставщики', 'url': '/suppliers/'},
    {'title': 'Заявка', 'url': '/application/'},
    {'title': 'Импорт', 'url': '/imports/'},
]


DATA_FILE = settings.BASE_DIR / 'sample_data.csv'


REQUIRED_COLUMNS = {
    'name',
    'category',
    'supplier',
    'purchase_price',
    'sale_price',
    'stock_quantity',
}


def import_page(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('database_file')

        if not uploaded_file:
            messages.error(request, 'Файл не выбран.')
            return redirect('import_page')

        if not uploaded_file.name.lower().endswith('.csv'):
            messages.error(request, 'Загрузите файл в формате CSV.')
            return redirect('import_page')

        file_bytes = uploaded_file.read()

        try:
            file_text = file_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            messages.error(request, 'Не удалось прочитать файл. Сохраните CSV в кодировке UTF-8.')
            return redirect('import_page')

        reader = csv.DictReader(io.StringIO(file_text))

        if not reader.fieldnames:
            messages.error(request, 'CSV-файл пустой или не содержит заголовков.')
            return redirect('import_page')

        current_columns = {
            column.strip()
            for column in reader.fieldnames
            if column
        }

        missing_columns = REQUIRED_COLUMNS - current_columns

        if missing_columns:
            messages.error(
                request,
                'В CSV отсутствуют колонки: ' + ', '.join(sorted(missing_columns))
            )
            return redirect('import_page')

        rows_count = 0

        for row in reader:
            if any((value or '').strip() for value in row.values()):
                rows_count += 1

        if rows_count == 0:
            messages.error(request, 'CSV-файл не содержит строк с товарами.')
            return redirect('import_page')

        DATA_FILE.write_bytes(file_bytes)

        messages.success(
            request,
            f'Файл успешно загружен. Импортировано строк: {rows_count}.'
        )

        return redirect('product_list')

    context = {
        'title': 'Импорт данных',
        'menu': MENU,
        'required_columns': sorted(REQUIRED_COLUMNS),
        'data_file_exists': DATA_FILE.exists(),
        'data_file_name': DATA_FILE.name,
    }

    return render(request, 'imports/imports.html', context)