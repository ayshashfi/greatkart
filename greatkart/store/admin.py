from django.contrib import admin
from .models import Product,Variation,ReviewRating,ProductGallery,Size,Color
import admin_thumbnails


# Register your models here.
@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model=ProductGallery
    extra=1
    
class ProductAdmin(admin.ModelAdmin):
    list_display=('product_name','product_price','category','modified_date','is_available','is_active','offer')
    prepopulated_fields={'slug':('product_name',)}
    inlines=[ProductGalleryInline]
    
class VariationAdmin(admin.ModelAdmin):
    list_display=('product','color','size','quantity','is_available')
    list_filter=('product','color','size')

admin.site.register(Product,ProductAdmin)
admin.site.register(Variation,VariationAdmin)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)
admin.site.register(Size)
admin.site.register(Color)