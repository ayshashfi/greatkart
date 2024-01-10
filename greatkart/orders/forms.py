from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model=Order
        fields=['first_name','last_name','phone','email','address_line_1','address_line_2','country','state','city','order_note']
        

class ReturnItemForm(forms.Form):
    item_name = forms.CharField(max_length=255)
    reason = forms.CharField(widget=forms.Textarea)
