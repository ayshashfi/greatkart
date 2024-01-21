from django.db import models
from category.models import category
from django.urls import reverse
from accounts.models import Account
from offer.models import Offer
from django.db.models import Avg, Count

# Create your models here.
class Color(models.Model):
    color_name = models.CharField(max_length=50, null=True)
    color_code = models.CharField(max_length=15, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.color_name


class Size(models.Model):
    size_range = models.CharField(max_length=60)
    colors_available = models.ManyToManyField(Color, related_name='available_sizes')
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.size_range


class Product(models.Model):
    product_name    = models.CharField(max_length=200, unique=True)
    slug            = models.SlugField(max_length=200, unique=True)
    description     = models.TextField(max_length=500, blank=True)
    product_price           = models.IntegerField()
    images          = models.ImageField(upload_to='photos/products',blank=True)
    is_available    = models.BooleanField(default=True)
    category        = models.ForeignKey(category, on_delete=models.CASCADE)
    created_date    = models.DateTimeField(auto_now_add=True)
    modified_date   = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, null=True )
    

    def get_url(self):
        return reverse('product_detail', args=[self.category.id, self.id])
    
       
    def get_unique_sizes(self):
        return self.variation_set.values_list('size__size_range', flat=True).distinct()

    def get_unique_colors(self):
        return self.variation_set.values_list('color__color_name', flat=True).distinct()

    def __str__(self):
        return self.product_name

    def averageReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg

    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count

class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category='color', is_active=True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size', is_active=True)

variation_category_choice = (
    ('color', 'color'),
    ('size', 'size'),
)

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE,null=True)
    size = models.ForeignKey(Size, on_delete=models.CASCADE,null=True)
    is_available           = models.BooleanField(default=True)
    quantity           = models.IntegerField(null=True,default=None)
    created_date        = models.DateTimeField(auto_now=True)


    objects = VariationManager()

    def __str__(self):
        return f"{self.product.product_name} - {self.color.color_name} - {self.size.size_range}"
    


class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject

    
    
class ProductGallery(models.Model):
    product=models.ForeignKey(Product,default=None,on_delete=models.CASCADE)
    image=models.ImageField(upload_to='photos/variants',max_length=255)  
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return self.product.product_name
    
    class Meta:
        verbose_name='productgallery'
        verbose_name_plural='product gallery'
        
        


    
    