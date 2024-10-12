from django import forms 
from . models import ReviewRating,Product, Variation, ProductGallery


class ReviewForm(forms.ModelForm):
    class Meta:
        model=ReviewRating
        fields=['subject','review','rating']
        
        

class ImageForm(forms.ModelForm):
    class Meta:
        model = ProductGallery
        fields = ('image',)
        
        



