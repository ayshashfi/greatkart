from django.contrib import admin
from . models import Payment,Order,OrderProduct,Notification
# Register your models here.

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    actions = ['mark_as_returned']
    list_display = ['order_number', 'full_name', 'phone', 'email', 'city', 'order_total', 'tax', 'status', 'is_ordered', 'created_at']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email']
    list_per_page = 20
    inlines = [OrderProductInline]
    
    def mark_as_returned(self, request, queryset):
        # Update the status of selected orders to 'Returned'
        queryset.update(status='Returned')
        
    mark_as_returned.short_description = 'Mark selected orders as Returned'

admin.site.register(Order,OrderAdmin)
admin.site.register(OrderProduct)
admin.site.register(Payment)
admin.site.register(Notification)