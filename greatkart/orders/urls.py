from django.urls import path
from . import views

urlpatterns =[
    path('place_order/',views.place_order,name='place_order'),
    path('payments/',views.payments,name='payments'),
    path('order_complete/', views.order_complete, name='order_complete'),
    path('order_list/', views.order_list, name='order_list'),
    path('update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('return/<int:order_id>/', views.return_item, name='return_item'),
    path('view_order_details/<str:order_number>/', views.view_order_details, name='view_order_details'),
    path('cod/<int:order_number>/', views.cod, name='cod'),
    path('cod_order_complete/<int:order_number>/', views.cod_order_complete, name='cod_order_complete'),
    path('download_invoice/<str:order_number>/', views.download_invoice_paypal, name='download_invoice'),
    path('download_invoice_cod/<str:order_number>/', views.download_invoice_cod, name='download_invoice_cod'),
    
    
]
