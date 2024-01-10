from django.urls import path
from . import views

urlpatterns = [
    path('admin_login/',views.admin_login,name='admin_login'),
    path('admin_dashboard/',views.admin_dashboard,name='admin_dashboard'),
    path('usermanagement/',views.usermanagement,name='usermanagement'),
    path('blockuser/<int:user_id>/',views.blockuser,name='blockuser'),
    
    path('admin_logout1/',views.admin_logout1,name='admin_logout1'),
    path('sales_report/',views.sales_report,name='sales_report'),
    path('generate_pdf/',views.generate_pdf,name='generate_pdf'),
    path('generate_excel/', views.generate_excel, name='generate_excel'),
   path('get_chart_data/', views.GetChartDataView.as_view(), name='get_chart_data'),
    
   
]
