"""
URL configuration for greatkart project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from . import views

from django.conf.urls import handler404
from store.views import custom_404

handler404 = custom_404



urlpatterns = [
    path('',views.store, name='store'),
    path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('search/',views.search,name='search'),
    path('products',views.products,name='products'),
    path('product_view/<int:product_id>', views.product_view, name='product_view'),
    path('addproduct/',views.addproduct,name='addproduct'),
    path('product_edit/<int:product_id>', views.product_edit, name='product_edit'),
    path('product_delete/<int:product_id>', views.product_delete, name='product_delete'),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('product_variant/',views.product_variant,name='product_variant'),
    path('product_size/',views.product_size,name='product_size'),
    path('add_size/',views.add_size,name='add_size'),
    path('edit_size/<int:size_id>/', views.edit_size, name='edit_size'),
    path('size_delete/<int:size_range_id>',views.size_delete,name='size_delete'),
    path('product_color/',views.product_color,name='product_color'),
    path('add_color/',views.add_color,name='add_color'),
    path('edit_color/<int:color_id>/', views.edit_color, name='edit_color'),
    path('color_delete/<int:color_name_id>/',views.color_delete,name='color_delete'),
    path('add_Product_Variant/',views.add_Product_Variant,name='add_Product_Variant'),
    path('edit_productvariant/<int:variant_id>/',views.edit_productvariant,name='edit_productvariant'),
    path('productvariant_delete/<int:variant_id>/',views.productvariant_delete,name='productvariant_delete'),
    path('image_view/<int:img_id>/',views.image_view,name='image_view'),
    path('image_list/<int:product_id>/',views.image_list,name='image_list'),
    path('image_delete/<int:image_id>/',views.image_delete,name='image_delete'),
    path('variant_search/',views.variant_search,name='variant_search'),
    path('product_variant_view/<int:product_id>/',views.product_variant_view,name='product_variant_view'),
    
] 
