from django.shortcuts import render,get_object_or_404,redirect
from .models import Product,Variation,ReviewRating,ProductGallery,Size,Color
from category.models import category
from carts.views import _cart_id
from carts.models import CartItem
from django.core.paginator import  Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from .forms import ReviewForm,ImageForm
from orders.models import OrderProduct
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
import webcolors


from django.db.models import  Case, Value, BooleanField
from django.db.models import Case, When, Value, BooleanField

def store(request, category_slug=None):
    categories = None
    products = None
    active_products = Product.objects.filter(is_active=True)
    if category_slug is not None:
        categories = get_object_or_404(category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True).order_by('id')
    else:
        products = Product.objects.filter(is_available=True).order_by('id')

    paginator = Paginator(products, 3)  # Change the second argument to set the number of products per page
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
        'active_products':active_products,
    }
    
    return render(request, 'store/store.html', context)

from django.db.models import F

def product_detail(request, category_slug, product_slug):
    try:
        single_product = get_object_or_404(Product, category__id=category_slug, id=product_slug, is_active=True)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id,is_available=True)

    # Get the variations with stock status
    variations = Variation.objects.filter(product=single_product).select_related('color', 'size').annotate(
    in_stock=Case(
        When(quantity__gt=0, then=Value(True)),
        default=Value(False),
        output_field=BooleanField()
    ),
    variation_quantity=F('quantity')  # Use a different name for the annotation
    ).distinct()

    
    colors = Color.objects.filter(variation__product=single_product, is_available=True).distinct()
    color_variations = []

    for color in colors:
        variations_for_color = Variation.objects.filter(product=single_product, color=color)
        color_variations.append({
        'color': color,
        'sizes': color.variation_set.filter(product=single_product).values_list('size__size_range', flat=True).distinct(),
        'product_id': single_product.id , # Include the product ID
        'variations': variations_for_color
    })


    # Get the offer related to the product
    product_offer = single_product.offer  # Assuming "offer" is the foreign key in the Product model
    
    # Calculate the discounted price
    discounted_price = single_product.product_price - product_offer.discount_amount if product_offer else None

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'color_variations': color_variations,
        'variations': variations,
        'product_offer': product_offer,
        'discounted_price': discounted_price,
    }

    print("Variations:")
    for variation in variations:
        print(f"ID: {variation.id}, Color: {variation.color}, Size: {variation.size}, Quantity: {variation.variation_quantity}")
    return render(request, 'store/product_detail.html', context)



def search(request):
    if 'keyword' in request.GET:
        keyword=request.GET['keyword']
        if keyword:
            products=Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword)|    Q(product_name__icontains=keyword))
            product_count=products.count()
    context={
        'products':products,
        'product_count':product_count,
    }    
    return render(request,'store/store.html',context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)
            
from datetime import datetime, date           
from orders.models import Notification       
@login_required(login_url='admin_login')
def products(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    product=Product.objects.all().order_by("id")
    p=Paginator(product,5)
    page=request.GET.get('page')
    product_page=p.get_page(page)
    page_nums='a'*product_page.paginator.num_pages
    notifications = Notification.objects.all().order_by('-timestamp')[:5]
    today_notifications = [notification for notification in notifications if notification.timestamp.date() == date.today()]
    product_list={
        'product':product,
        'categories':category.objects.filter(is_available=True).order_by('id'),
        'offer': Offer.objects.filter(is_available= True).order_by('id'),
        'product_page':product_page,
        'page_nums':page_nums,
        'notifications':notifications,
        'today_notifications':today_notifications,
        
    }
    return render (request,'store/product.html',product_list)



@login_required(login_url='admin_login')
def product_view(request,product_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    
    variant=Variation.objects.all()
    size_range=Size.objects.filter(is_available=True).order_by('id')
    color_name=Color.objects.filter(is_available=True).order_by('id')
    product=Product.objects.filter(is_available=True).order_by('id')

    variant_list={
        'variant':variant,
        'size_range':size_range,
        'color_name':color_name,
        'product':product

    }
    return render(request,'store/product_view.html',{'variant_list':variant_list})
            

from offer.models import Offer

@login_required(login_url='admin_login')
def addproduct(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    categories = category.objects.all()
    product_offers = Offer.objects.all()

    if request.method == 'POST':
        name = request.POST['product_name']
        image = request.FILES.get('image', None)
        price = request.POST['product_price']
        category_id = request.POST.get('category')
        offer_id = request.POST.get('offer')
        product_description = request.POST.get('description')

        # Validation
        if Product.objects.filter(product_name=name).exists():
            check = Product.objects.get(product_name=name)
            if check.is_available == False:
                check.product_name += check.product_name
                check.slug += check.slug
                check.save()
            else:    
                messages.error(request, 'Product name already exists')
                return redirect('products')
      
        if name.strip() == '' or price.strip() == '':
            messages.error(request, "Name or Price field are empty!")
            return redirect('products')
       
        category_obj = category.objects.get(id=category_id)
        if offer_id == '':
            offer_obj = None
        else:    
            offer_obj = Offer.objects.get(id=offer_id)
             
        product = Product(
            product_name=name,
            category=category_obj,
            offer=offer_obj,
            product_price=price,
            slug=name,
            description=product_description,
            images=image,
        )
        product.save()
        messages.success(request, 'Product added successfully!')
        return redirect('products')

    return render(request, 'store/product.html', {'categories': categories, 'product_offers': product_offers})



@login_required(login_url='admin_login')
def product_edit(request, product_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    if request.method == 'POST':
        name = request.POST['product_name']
        image = request.FILES.get('image', None)
        price = request.POST['product_price']
        category_id = request.POST.get('category')
        offer_id = request.POST.get('offer')
        product_description = request.POST.get('description', '')

        if name.strip() == '' or price.strip() == '':
            messages.error(request, 'Fields cannot be empty!')
            return redirect('products')

        category_obj = category.objects.get(id=category_id)

        # Check if offer_id is empty before attempting to retrieve offer_obj
        if offer_id == '':
            offer_obj = None
        else:
            try:
                offer_obj = Offer.objects.get(id=offer_id)
            except Offer.DoesNotExist:
                messages.error(request, 'Selected offer does not exist!')
                return redirect('products')

        if Product.objects.filter(product_name=name).exclude(id=product_id).exists():
            messages.error(request, 'Product name already exists!')
            return redirect('products')

        editproduct = Product.objects.get(id=product_id)
        editproduct.product_name = name
        editproduct.product_price = price
        editproduct.category = category_obj
        editproduct.offer = offer_obj
        editproduct.description = product_description
        editproduct.images=image
        editproduct.save()
        messages.success(request, 'Product edited successfully!')
        return redirect('products')

    return render(request, 'store/product.html')



    
    
@login_required(login_url='admin_login')
def product_delete(request,product_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    delete_product=Product.objects.get(id=product_id)
    variants=Variation.objects.filter(product=delete_product)
    if delete_product.is_available:
        for variant in variants:
            variant.is_available= False
            variant.quantity=0
            variant.save()
        delete_product.is_available=False
        delete_product.is_active=False
        delete_product.save()
        messages.success(request,'product deleted successfully!')
    else:
        for variant in variants:
            variant.is_available= True
            variant.quantity=0
            variant.save()
        delete_product.is_available=True
        delete_product.is_active=True
        delete_product.save()
        messages.success(request,'product added successfully!')
    return redirect('products') 



@login_required(login_url='admin_login')
def product_variant(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    
    variant = Variation.objects.all().order_by("id")
    size_range= Size.objects.all()
    color_name= Color.objects.all()
    product=Product.objects.all()
    product_gallery = ProductGallery.objects.all()
    p=Paginator(variant,8)
    page=request.GET.get('page')
    variant_page=p.get_page(page)
    page_nums='a'*variant_page.paginator.num_pages
    variant_list={
        'variant'    :variant,
        'size_range' :size_range,
        'color_name' :color_name, 
        'product'   :product,
        'variant_page':variant_page,
        'page_nums':page_nums,
        'product_gallery': product_gallery,
    }
    return render(request,'variant/variant.html',{'variant_list':variant_list}) 




@login_required(login_url='admin_login')  
def add_Product_Variant(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    if request.method == 'POST':
        variant_name = request.POST.get('variant_name')
        variant_size = request.POST.get('variant_size')
        variant_color = request.POST.get('variant_color')
        variant_quantity = request.POST.get('variant_quantity')

        # Validation
        if variant_quantity.strip() == '':
            messages.error(request, "Quantity field is empty!")
            return redirect('product_variant')

        try:
            product_obj = Product.objects.get(id=variant_name)
            size_obj = Size.objects.get(id=variant_size)
            color_obj = Color.objects.get(id=variant_color)

            # Check if variant already exists
            if Variation.objects.filter(product=product_obj, size=size_obj, color=color_obj).exists():
                messages.error(request, "Variant with the same product, size, and color already exists!")
                return redirect('product_variant')

            # Save new variant
            add_variant = Variation(
                product=product_obj,
                color=color_obj,
                size=size_obj,
                quantity=variant_quantity,
            )
            add_variant.save()

            messages.success(request, 'Variant added successfully!')
            return redirect('product_variant')

        except ObjectDoesNotExist:
            messages.error(request, "Invalid product, size, or color selected!")
            return redirect('product_variant')

    return render(request, 'variant/variant.html')


 
@login_required(login_url='admin_login')  
def edit_productvariant(request,variant_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    
    if request.method == 'POST':
        variant_name = request.POST.get('variant_name')
        variant_size = request.POST.get('variant_size')
        variant_color = request.POST.get('variant_color')
        variant_quantity = request.POST.get('variant_quantity')
        
        if variant_quantity.strip() == '':
            messages.error(request, "Quantity field is empty!")
            return redirect('product_variant')
        
     
        product_obj = Product.objects.get(id=variant_name)
        size_obj = Size.objects.get(id=variant_size)
        color_obj = Color.objects.get(id=variant_color)

        # Check if variant already exists
        if Variation.objects.filter(product=product_obj, size=size_obj, color=color_obj).exists():
            check = Variation.objects.get(id=variant_id)
            if product_obj==check.product and size_obj==check.size and color_obj==check.color:
                pass
            else:
                messages.error(request, "Variant with the same product, size, and color already exists!")
                return redirect('product_variant')
        
        edit_variant=Variation.objects.get(id=variant_id)
        edit_variant.color=color_obj
        edit_variant.size=size_obj
        edit_variant.product=product_obj
        edit_variant.quantity=variant_quantity
        edit_variant.save()
        messages.success(request,'product edited successfully!')
        
        return redirect('product_variant')
    
    
    
    
@login_required(login_url='admin_login')
def productvariant_delete(request, variant_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    delete_productvariant = Variation.objects.get(id=variant_id)

    if delete_productvariant.is_available:
        # If the product variant is currently available, unlist it
        delete_productvariant.is_available = False
        delete_productvariant.quantity = 0
        delete_productvariant.save()
        messages.success(request, 'Product variant unlisted successfully!')
    else:
        # If the product variant is not available, list it
        delete_productvariant.is_available = True
        delete_productvariant.save()
        messages.success(request, 'Product variant listed successfully!')

    return redirect('product_variant')




@login_required(login_url='admin_login')  
def image_list(request,product_id):  
    image=ProductGallery.objects.filter(product=product_id,is_available =True)
    add_image =product_id
    return render(request,'variant/image_management.html',{'image':image,'add_image':add_image})



from django.shortcuts import render, redirect
from .forms import ImageForm
from .models import Product

@login_required(login_url='admin_login')  
def image_view(request, img_id):
    
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        var = Product.objects.get(id=img_id)

        if form.is_valid():
            # Get crop data from the form
            crop_x = request.POST.get('crop_x')
            crop_y = request.POST.get('crop_y')
            crop_width = request.POST.get('crop_width')
            crop_height = request.POST.get('crop_height')

            # Create an Image instance without saving it to the database
            image_instance = form.save(commit=False)

            # Set the product for the image
            image_instance.product = var

            # Perform cropping based on the provided crop data
            image_instance.image = crop_and_save_image(image_instance.image, crop_x, crop_y, crop_width, crop_height)

            # Save the Image instance to the database
            image_instance.save()

            print("Image saved successfully!")
            
            return redirect('image_list', product_id=img_id)
       
    else:
        form = ImageForm()
    
    context = {'form': form, 'img_id': img_id}
    return render(request, 'variant/image_add.html', context)

from PIL import Image
from io import BytesIO

def crop_and_save_image(original_image, crop_x, crop_y, crop_width, crop_height):
    # Open the original image using PIL
    image = Image.open(original_image)

    # Crop the image based on the provided crop data
    cropped_image = image.crop((float(crop_x), float(crop_y), float(crop_x) + float(crop_width), float(crop_y) + float(crop_height)))

    # Save the cropped image to a BytesIO buffer
    buffer = BytesIO()
    cropped_image.save(buffer, format='PNG')

    # Set the buffer's position to the beginning
    buffer.seek(0)

    # Update the original image content with the cropped image content
    original_image.file = buffer

    return original_image





@login_required(login_url='admin_login')
def image_delete(request, image_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    try:
        delete_image = ProductGallery.objects.get(id=image_id)
        var_id = delete_image.product.id 
        delete_image.is_available = False
        delete_image.save()
        messages.success(request, 'Image deleted successfully!')
     
        return redirect('image_list', product_id=var_id)

    except:
        return redirect('product_variant')

 
       
       
@login_required(login_url='admin_login')         
def product_variant_view(request,product_id):
    if not request.user.is_superuser:
        return redirect('admin_login')
  
    variant=ProductGallery.objects.filter(variant__product=product_id ,is_available=True)
    size_range= Size.objects.filter(is_available=True).order_by('id')
    color_name= Color.objects.filter(is_available=True).order_by('id')
    product=Product.objects.filter(is_available=True).order_by('id')
    variant_list={
        'variant'    :variant,
        'size_range' :size_range,
        'color_name' :color_name, 
         'product'   :product,
         
    }
    # variant_id
    return render(request,'variant/variant_view.html',{'variant_list':variant_list})




@login_required(login_url='admin_login1')  
def variant_search(request):
    search = request.POST.get('search')
    if search is None or search.strip() == '':
        messages.error(request,'Filed cannot empty!')
        return redirect('product_variant')
    variant = Variation.objects.filter( Q(product__product_name__icontains=search) | Q(color__color_name__icontains=search) |Q(size__size_range__icontains=search)| Q(quantity__icontains=search), is_available=True) 
    size_range= Size.objects.filter(is_available=True).order_by('id')
    color_name= Color.objects.filter(is_available=True).order_by('id')
    product=Product.objects.filter(is_available=True).order_by('id')
    variant_list={
        'variant'    :variant,
        'size_range' :size_range,
        'color_name' :color_name, 
         'product'   :product,
    }
    if variant :
        pass
        return render(request,'variant/variant.html',{'variant_list':variant_list}) 
    else:
        variant:False
        messages.error(request,'Search not found!')
        return redirect('product_variant') 
    
    
    
    
@login_required(login_url='admin_login')      
def product_size(request):
    if not request.user.is_superadmin:
            return redirect('admin_login')   
    products_size=Size.objects.all().order_by('id')
    p=Paginator(products_size,6)
    page=request.GET.get('page')
    size_page=p.get_page(page)
    page_nums='a'*size_page.paginator.num_pages
    return render(request,'variant/size_management.html',{'products_size':products_size,'size_page':size_page,'page_nums':page_nums})



@login_required(login_url='admin_login')  
def add_size(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    if request.method == 'POST':
        size = request.POST.get('size')  
        if  size.strip() == '':
            messages.error(request, 'Field cannot be empty!')
            return redirect('product_size')

        if Size.objects.filter(size_range=size).exists():
            messages.error(request, 'Size already exists')
            return redirect('product_size')

        size_object = Size(size_range=size)
        size_object.save()
        messages.success(request,'Size added successfully!')
        return redirect('product_size')

    return render(request, 'variant/size_management.html')



login_required(login_url='admin_login')
def edit_size(request, size_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    size = Size.objects.get(pk=size_id)

    if request.method == 'POST':
        size_range = request.POST.get('size')

        if size_range.strip() == '':
            messages.error(request, 'Field cannot be empty!')
            return redirect('product_size')

        size.size_range = size_range
        size.save()

        messages.success(request, 'Size edited successfully!')

        return redirect('product_size')

    return render(request, 'variant/size_management.html', {'size': size})



@login_required(login_url='admin_login')  
def size_delete(request, size_range_id):  
    if not request.user.is_superadmin:
        return redirect('admin_login')
    delete_size = Size.objects.get(id=size_range_id) 
    if delete_size.is_available:
        delete_size.is_available=False
        delete_size.save()
        messages.success(request,'Size deleted successfully!')
    else:
        delete_size.is_available=True
        delete_size.save()
        messages.success(request,'Size added successfully!')
    
    return redirect('product_size') 




def product_color(request):
    if not request.user.is_superadmin:
            return redirect('admin_login')   
    products_color=Color.objects.all().order_by('id')
    p=Paginator(products_color,5)
    page=request.GET.get('page')
    color_page=p.get_page(page)
    page_nums='a'*color_page.paginator.num_pages
    return render(request,'variant/color_management.html',{'products_color':products_color,'color_page':color_page,'page_nums':page_nums})



def get_color_name(color_code):
    try:
        color_name = webcolors.rgb_to_name(webcolors.hex_to_rgb(color_code))
        return color_name
    except ValueError:
        return "Unknown"
    
    
    
def add_color(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    if request.method == 'POST':
        colorname = request.POST.get('color1')  
        color = request.POST.get('color')  
        color1=color
        
        color= get_color_name(color)
        if color == "Unknown":
            color=color1
        
        if colorname.strip() == '':
            messages.error(request, 'Field cannot be empty!')
            return redirect('product_color')

        if Color.objects.filter(Q(color_name__iexact=colorname) | Q(color_name__iexact=colorname)).exists():
            color_add = Color.objects.get(color_name__iexact=colorname)
            if not color_add.is_available:
                pass
            else:
                messages.error(request, 'Color already exists!')
                return redirect('product_color')

        color_object = Color(color_name=colorname,color_code=color)
        color_object.save()
        
        messages.success(request,'color add successfully!')

        return redirect('product_color')

    return render(request, 'color_management/color_management.html')



def edit_color(request, color_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    color = Color.objects.get(pk=color_id)

    if request.method == 'POST':
        colorname = request.POST.get('color1')
        color_code = request.POST.get('color')

        color_name_from_code = get_color_name(color_code)
        if color_name_from_code == "Unknown":
            color_name_from_code = colorname

        if colorname.strip() == '':
            messages.error(request, 'Field cannot be empty!')
            return redirect('product_color')

        # Check if the edited color name already exists (excluding the current color)
        if Color.objects.filter(color_name=color_name_from_code).exclude(id=color.id).exists():
            messages.error(request, 'Color with the same name already exists!')
            return redirect('product_color')

        color.color_name = color_name_from_code
        color.color_code = color_code
        color.save()

        messages.success(request, 'Color edited successfully!')

        return redirect('product_color')

    return render(request, 'color_management/color_management.html', {'color': color})



def color_delete(request, color_name_id):  
    if not request.user.is_superadmin:
        return redirect('admin_login')
    delete_color = Color.objects.get(id=color_name_id) 
    if delete_color.is_available:
        delete_color.is_available=False
        delete_color.save()
        messages.success(request,'Color deleted successfully!')
    else:
        delete_color.is_available=True
        delete_color.save()
        messages.success(request,'Color added successfully!')
    
    return redirect('product_color') 



from django.shortcuts import render

def custom_404(request, exception=None):
    return render(request, 'includes/404.html', status=404)

