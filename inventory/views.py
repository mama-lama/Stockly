from django.shortcuts import render
from .models import Inventory

# Create your views here.
def inventory_list(request):
    ''' Заглушка '''
    items = Inventory.objects.select_related('product').all()
    context = {'items': items}
    return render(request, 'inventory/list.html', context)
