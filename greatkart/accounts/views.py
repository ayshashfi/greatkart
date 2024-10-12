from django.shortcuts import render,redirect,get_object_or_404
from .forms import RegistrationForm,UserForm,UserProfileForm
from .models import Account,UserProfile,Address
from orders.models import Order,OrderProduct
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required

#veification
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.http import HttpResponse

from carts.views import _cart_id
from carts.models import Cart,CartItem
import requests

from django.http import JsonResponse




def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            # Create a user profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-user.png'
            profile.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            # messages.success(request, 'Thank you for registering with us. We have sent you a verification email to your email address. Please verify it.')
            return redirect('/accounts/login/?command=verification&email='+email)
    else:
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)


    

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
       
        
        user = auth.authenticate(email=email, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, 'Your account is blocked by admin!!')
                return redirect('login')

            auth.login(request, user)
            messages.success(request, 'You are now logged in.')

            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
            except Cart.DoesNotExist:
                cart = Cart.objects.create(cart_id=_cart_id(request))

            is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()

            if is_cart_item_exists:
                cart_items = CartItem.objects.filter(cart=cart)

                for cart_item in cart_items:
                    existing_variation = set(cart_item.variations.all())
                    user_cart_items = CartItem.objects.filter(user=user)

                    for user_cart_item in user_cart_items:
                        if set(user_cart_item.variations.all()) == existing_variation:
                            user_cart_item.quantity += cart_item.quantity
                            user_cart_item.save()
                            break
                    else:
                        CartItem.objects.create(
                            cart=cart,
                            user=user,
                            quantity=cart_item.quantity,
                            variations=cart_item.variations.all()
                        )

            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)

            except:
                return redirect('home')
            login(request, user)
            return HttpResponse('Logged in successfully')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')

    return render(request, 'accounts/login.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, "You are now logged out.")
    return redirect('login')



def activate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None
        
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active=True
        user.save()
        messages.success(request,'Congratulations! Your account is activated')
        return redirect('login')
    else:
        messages.error(request,'Invalid activation link')
        return redirect('register')  
    
     
    

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()

    # Check if the user is a superadmin
    if request.user.is_superadmin:
        # If the user is a superuser, create or get their profile
        userprofile, created = UserProfile.objects.get_or_create(
            user_id=request.user.id,
            defaults={'address_line_1': 'Default Address'}
        )
    else:
        # If the user is a regular user, get their profile using get_object_or_404
        userprofile = get_object_or_404(UserProfile, user_id=request.user.id)

    context = {
        'orders_count': orders_count,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/dashboard.html', context)

   



def forgotPassword(request):
    if request.method=='POST':
        email=request.POST['email']
        if Account.objects.filter(email=email).exists():
            user=Account.objects.get(email__exact=email)
            #reset password
            current_site = get_current_site(request)
            mail_subject = 'Please reset your password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            
            messages.success(request,'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request,'Account does not exist!')    
            return redirect('forgotPassword')
    return render (request, 'accounts/forgotPassword.html')   



def resetpassword_validate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None
    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid']=uid
        messages.success(request,'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request,'This link has been expired!')
        return redirect('login')
    
    
    

def resetPassword(request):
    if request.method =='POST':
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']
        
        if password==confirm_password:
            uid=request.session.get('uid')
            user=Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request,'Password reset successful')
            return redirect('login')
        else:
            messages.error(request,'Password do not match!')
            return redirect('resetPassword')
    else:
        return render(request,'accounts/resetPassword.html')
    
    
    
@login_required(login_url='login')  
def my_orders(request):
    orders=Order.objects.filter(user=request.user,is_ordered=True).order_by('-created_at')
    context={
        'orders':orders,
    }
    return render(request,"accounts/my_orders.html",context)



@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/edit_profile.html', context)




@login_required(login_url='login')
def change_password(request):
    if request.method=='POST':
        current_password=request.POST['current_password']
        new_password=request.POST['new_password']
        confirm_password=request.POST['confirm_password']
        
        user=Account.objects.get(username__exact=request.user.username)
        
        if new_password==confirm_password:
            success=user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                #auth.logout(request)
                messages.success(request,'Password updated sucessfully.')
                return redirect('change_password')
            else:
                messages.error(request,'Please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request,'Password does not match!')
            return redirect('change_password')
    return render(request, 'accounts/change_password.html')



    
@login_required(login_url='login') 
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'accounts/order_detail.html', context)



from django.db.models import Max

def my_addresses(request):
    unique_saved_addresses = (
        Address.objects
        .filter(user=request.user, is_saved_address=True)
        .values('address_line_1', 'city', 'state', 'country')
        .annotate(max_id=Max('id'))
    )

    # Get the latest saved address for each unique set of fields
    saved_addresses = Address.objects.filter(id__in=unique_saved_addresses.values('max_id'))

    context = {
        'saved_addresses': saved_addresses,
    }
    return render(request, "accounts/my_addresses.html", context)



def get_address_details(request):
    if request.method == 'GET':
        address_id = request.GET.get('address_id')
        address = get_object_or_404(Address, id=address_id)

        data = {
            'first_name': address.first_name,
            'last_name': address.last_name,
            'phone': address.phone,
            'email': address.email,
            'address_line_1': address.address_line_1,
            'address_line_2': address.address_line_2,
            'country': address.country,
            'state': address.state,
            'city': address.city,
            'pincode': address.pincode,
            'order_note': address.order_note,
        }
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'Invalid request method'})



from django.views.decorators.csrf import csrf_exempt

@login_required
@csrf_exempt  # Disable CSRF for simplicity, consider enabling it in a real project
def save_edited_address(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        address = get_object_or_404(Address, id=address_id)

        # Update address fields with the edited data
        address.first_name = request.POST.get('first_name', address.first_name)
        address.last_name = request.POST.get('last_name', address.last_name)
        address.phone = request.POST.get('phone', address.phone)
        address.email = request.POST.get('email', address.email)
        address.address_line_1 = request.POST.get('address_line_1', address.address_line_1)
        address.address_line_2 = request.POST.get('address_line_2', address.address_line_2)
        address.country = request.POST.get('country', address.country)
        address.state = request.POST.get('state', address.state)
        address.city = request.POST.get('city', address.city)
        address.pincode = request.POST.get('pincode', address.pincode)
        address.order_note = request.POST.get('order_note', address.order_note)

        # Save the updated address
        address.save()

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error': 'Invalid request method'})


# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Address

@require_POST
def delete_address(request):
    # Assuming you have a model named Address with an 'id' field
    address_id = request.POST.get('address_id')
    
    # Retrieve the address object
    address = get_object_or_404(Address, id=address_id)
    
    # Delete the address
    address.delete()
    
    return JsonResponse({'message': 'Address deleted successfully'})












