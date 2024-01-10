from django.urls import path
from . import views

urlpatterns=[
  path('category/', views.categories, name='categories'),
  path('category_search/', views.category_search, name='category_search'),
  path('add_category/', views.add_category, name='add_category'),
  path('editcategory/<slug:editcategory_id>', views.editcategory, name='editcategory'),
  path('deletecategory/<slug:deletecategory_id>', views.deletecategory, name='deletecategory'),
 

]
    