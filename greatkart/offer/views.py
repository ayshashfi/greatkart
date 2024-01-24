
from django.shortcuts import render, get_object_or_404, redirect
from .models import Offer
from django.contrib import messages
from datetime import datetime
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from datetime import datetime, date           
from orders.models import Notification

@login_required(login_url='admin_login')
def product_offer(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    offer=Offer.objects.all()
    p=Paginator(offer,5)
    page=request.GET.get('page')
    offer_page=p.get_page(page)
    page_nums='a'*offer_page.paginator.num_pages
    notifications = Notification.objects.all().order_by('-timestamp')[:5]
    today_notifications = [notification for notification in notifications if notification.timestamp.date() == date.today()]
    return render(request,'offer/product_offer.html',{'offer':offer, 'page_nums':page_nums,'offer_page':offer_page,'notifications':notifications,'today_notifications':today_notifications})


@login_required(login_url='admin_login')
def add_new_product_offer(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    if request.method == 'POST':
        offername = request.POST.get('offer_name')
        discount = request.POST.get('discount_amount')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if not offername or not offername.strip():
            messages.error(request, 'Field should not be empty!')
            return redirect('product_offer')

        if not discount or not discount.strip():
            messages.error(request, 'Field should not be empty!')
            return redirect('product_offer')

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format. Use YYYY-MM-DD!')
            return redirect('product_offer')

        if start_date >= end_date:
            messages.error(request, 'Start date must be before end date.')
            return redirect('product_offer')

        if start_date < timezone.now().date():
            messages.error(request, 'Enter a valid start date.')
            return redirect('product_offer')

        Offer.objects.create(
            offer_name=offername,
            discount_amount=discount,
            start_date=start_date,
            end_date=end_date,
            is_available=True  
        )
        messages.success(request, 'Product offer added successfully!')
        return redirect('product_offer')  

    return render(request, 'offer/product_offer.html')  
        
        
@login_required(login_url='admin_login')
def delete_product_offer(request,delete_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    try:    
        offer=Offer.objects.get(id=delete_id)
        offer.is_available=False
        offer.save()
        messages.success(request,'Offer successfully deleted!')
    except offer.DoesNotExist:
        messages.error(request,'Offer doesnot exist!')

    return redirect('product_offer')



def list_product_offer(request, offer_id):
    # Retrieve the product offer instance
    product_offer = get_object_or_404(Offer, id=offer_id)

    # Toggle the is_available attribute
    product_offer.is_available = not product_offer.is_available
    product_offer.save()

    # Redirect back to the product_offer page or any other desired page
    return redirect('product_offer')



@login_required(login_url='admin_login')
def edit_product_offer(request,edit_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    if request.method == 'POST':
        offername = request.POST.get('offer_name')
        discount = request.POST.get('discount_amount')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')

        if offername is None or offername.strip() == '':
            messages.error(request, "Order name cannot be blank.")
            return redirect('product_offer')
        if discount.strip() == '':
            messages.error(request, "Cannot blank Offer field")
            return redirect('product_offer')
        if Offer.objects.filter(offer_name=offername ,is_available=True).exclude(id=edit_id).exists():
            messages.error(request, 'Offer name already exists')
            return redirect('product_offer')
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Invalid date format. Use YYYY-MM-DD.")
            return redirect('product_offer')
        if start_date >= end_date:
            messages.error(request, "Start date must be before end date.")
            return redirect('product_offer')
        if start_date < timezone.now().date():
            messages.error(request, "Start date cannot be in the past.")
            return redirect('product_offer')
        
        off = Offer.objects.get(id=edit_id)
        off.offer_name = offername
        off.discount_amount = discount
        off.start_date = start_date
        off.end_date = end_date
        off.save()
        messages.success(request, "Offer edited successfully!")
        return redirect('product_offer')
    offers : Offer.objects.get(id=edit_id)
    context ={ 
     'offer':offers,
    }
    return render(request, 'offer/product_offer.html', context)


