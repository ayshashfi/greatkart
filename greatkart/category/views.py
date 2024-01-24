from django.shortcuts import render, redirect
from store.models import Product,Variation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import category
from django.http import Http404
from datetime import datetime, date           
from orders.models import Notification  


@login_required(login_url='admin_login')
def categories(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    categories = category.objects.filter().order_by('category_name')
    p=Paginator(categories,5)
    page=request.GET.get('page')
    product_page=p.get_page(page)
    page_nums='a'*product_page.paginator.num_pages
    notifications = Notification.objects.all().order_by('-timestamp')[:5]
    today_notifications = [notification for notification in notifications if notification.timestamp.date() == date.today()]
    return render(request, 'category/category.html', {'categories': categories,'product_page':product_page,
        'page_nums':page_nums,'notifications':notifications,'today_notifications':today_notifications})


@login_required(login_url='admin_login')
def add_category(request):
    try:
        if not request.user.is_superadmin:
            return redirect('admin_login')

        if request.method == 'POST':
            image = request.FILES.get('image', None)
            name = request.POST['category_name']
            description = request.POST['description']
            
            # Validation
            if name.strip() == '':
                messages.error(request, 'Name Not Found!')
                return redirect('categories')

            if category.objects.filter(category_name__iexact=name).exists():
                messages.error(request, 'Category name already exists')
                return redirect('categories')
            # Save
            if not image:
                messages.error(request, 'Image not uploaded')
                return redirect('categories')

            new_category = category(category_name=name, description=description, cat_image=image)
            new_category.save()
            messages.success(request,'category added successfully!')
            return redirect('categories')
    except:
            return redirect('categories')
       



@login_required(login_url='admin_login')
def editcategory(request, editcategory_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    try:
        # Retrieve the category instance to be edited
        category_instance = category.objects.get(slug=editcategory_id)

        if request.method == 'POST':
            # Process the form data if the request method is POST
            name = request.POST.get('category_name')
            description = request.POST.get('description')
            image = request.FILES.get('image', None)

            # Validation
            if name.strip() == '':
                messages.error(request, 'Name Not Found!')
                return redirect('categories')

            if category.objects.exclude(id=category_instance.id).filter(category_name=name).exists():
                messages.error(request, 'Category name already exists')
                return redirect('categories')

            # Save
            category_instance.category_name = name
            category_instance.description = description

            if image:
                category_instance.cat_image = image

            category_instance.save()
            messages.success(request, 'Category edited successfully!')
            return redirect('categories')

    except category.DoesNotExist:
        raise Http404("Category does not exist")  # Or redirect to an error page
    return render(request, 'category.html', {'category_instance': category_instance})



@login_required(login_url='admin_login')
def deletecategory(request,deletecategory_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    categery = category.objects.get(slug=deletecategory_id)
    products = Product.objects.filter(category=categery)
    if categery.is_available:
        for product in products:
            product.is_available = False
            product.save()

            variants = Variation.objects.filter(product=product)
            for variant in variants:
                variant.is_available = False
                variant.quantity = 0
                variant.save()
        categery.is_available = False
        categery.save()
        messages.success(request,'category deleted successfully!')
    else:
        for product in products:
            product.is_available = True
            product.save()

            variants = Variation.objects.filter(product=product)
            for variant in variants:
                variant.is_available = True
                variant.quantity = 0
                variant.save()
        categery.is_available = True
        categery.save()
        messages.success(request,'category added successfully!')
    return redirect('categories')



@login_required(login_url='admin_login')
def category_search(request):
    search = request.POST.get('search')
    if search is None or search.strip() == '':
        messages.error(request,'Filed cannot empty!')
        return redirect('categories')
    categories = category.objects.filter(category_name__icontains=search,is_available=True )
    if categories :
        pass
        return render(request, 'category/category.html', {'categories': categories})
    else:
        categories=False
        messages.error(request,'Search not found!')
        return redirect('categories')



