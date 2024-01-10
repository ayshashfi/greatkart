# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('product_offer/',views.product_offer,name='product_offer'),
    path('add_new_product_offer/',views.add_new_product_offer,name='add_new_product_offer'),
    path('delete_product_offer/<int:delete_id>/',views.delete_product_offer,name='delete_product_offer'),
    path('edit_product_offer/<int:edit_id>/',views.edit_product_offer,name='edit_product_offer'),
    path('list_product_offer/<int:offer_id>/', views.list_product_offer, name='list_product_offer'),
]
 

