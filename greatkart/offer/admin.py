from django.contrib import admin
# from .models import ProductOffer,CategoryOffer,ReferralOffer
# Register your models here.



# admin.py


# admin.site.register(ProductOffer)
# admin.site.register(CategoryOffer)
# admin.site.register(ReferralOffer)


from .models import Offer
 
admin.site.register(Offer)