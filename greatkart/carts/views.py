from django.shortcuts import render,redirect,get_object_or_404
from store.models import Product,Variation
from .models import Cart,CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect


def _cart_id(request):
    cart=request.session.session_key
    if not cart:
        cart=request.session.create()
    return cart


from django.shortcuts import render, redirect
from .models import Cart, CartItem, Variation, Product

def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)

    if request.method == 'POST':
        selected_color = request.POST.get('color')
        selected_size = request.POST.get('size')

    # If the user is authenticated
    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key,
                                                     variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass

        is_cart_item_exists = CartItem.objects.filter(
            product=product,
            user=current_user,
            selected_color=selected_color,
            selected_size=selected_size
        ).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.get(
                product=product,
                user=current_user,
                selected_color=selected_color,
                selected_size=selected_size
            )
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
                selected_color=selected_color,
                selected_size=selected_size,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

        # Calculate discounted price for the product in the cart
        discounted_price = product.product_price - (product.offer.discount_amount if product.offer else 0)

    # If the user is not authenticated
    else:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key,
                                                     variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=_cart_id(request)
            )
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(
            product=product,
            cart=cart,
            selected_color=selected_color,
            selected_size=selected_size
        ).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.get(
                product=product,
                cart=cart,
                selected_color=selected_color,
                selected_size=selected_size
            )
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
                selected_color=selected_color,
                selected_size=selected_size,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

        # Calculate discounted price for the product in the cart
        discounted_price = product.product_price - (product.offer.discount_amount if product.offer else 0)

    # Print discounted price for debugging
    print("Discounted price:", discounted_price)

    return redirect('cart')


   
   

def remove_cart(request,product_id,cart_item_id):
    product=get_object_or_404(Product,id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item=CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
        else:
            cart=Cart.objects.get(cart_id=_cart_id(request))
               
            cart_item=CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
        if cart_item.quantity>1:
            cart_item.quantity -=1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')




def remove_cart_item(request,product_id,cart_item_id):
    product=get_object_or_404(Product,id=product_id)
    if request.user.is_authenticated:
        cart_item=CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
    else:
        cart=Cart.objects.get(cart_id=_cart_id(request)) 
        cart_item=CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
    cart_item.delete()
    return redirect('cart')




from django.db.models import F, ExpressionWrapper, DecimalField

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            # Check if the product has an offer
            if cart_item.product.offer:
                # Calculate the discounted price for the current item
                discounted_price = ExpressionWrapper(
                    F('product__product_price') - F('product__offer__discount_amount'),
                    output_field=DecimalField()
                )

                # Update the cart item with the discounted price
                cart_item.discounted_price = discounted_price
                cart_item.save()

                # Add the discounted price to the total
                total += (cart_item.discounted_price * cart_item.quantity)
            else:
                # If there is no offer, use the regular product price for the total
                total += (cart_item.product.product_price * cart_item.quantity)

            quantity += cart_item.quantity

        # Calculate tax and grand total
        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)




from django.db import IntegrityError
from django.db.models import Max

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    current_user = request.user
    cart_items = CartItem.objects.filter(cart__cart_id=_cart_id(request))
    # Ensure that you pass variations to the template
    variations = [item.variations.all() for item in cart_items]

    # Filter out duplicate addresses for the current user
    unique_addresses = Address.objects.filter(
        user=current_user, is_saved_address=True
    ).values('address_line_1', 'city', 'state', 'country').annotate(max_id=Max('id'))

    # Get the latest saved address for each unique set of fields
    saved_addresses = Address.objects.filter(id__in=unique_addresses.values('max_id'))

    try:
        tax = 0
        grand_total = 0

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.product_price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass

    # Initialize selected_address to None
    selected_address = None

    # If a new address is submitted through the request, try to create it
    if request.method == 'POST':
        address_data = {
            'address_line_1': request.POST.get('address_line_1', ''),
            'city': request.POST.get('city', ''),
            'state': request.POST.get('state', ''),
            'country': request.POST.get('country', ''),
            # Add other fields as needed
        }

        # Check if an identical address already exists for the user
        existing_address = Address.objects.filter(
            user=current_user,
            address_line_1=address_data['address_line_1'],
            city=address_data['city'],
            state=address_data['state'],
            country=address_data['country'],
        ).first()

        if existing_address:
            # Address already exists, use the existing one
            selected_address = existing_address
        else:
            # Address is unique, create a new one
            try:
                new_address = Address.objects.create(
                    user=current_user,
                    address_line_1=address_data['address_line_1'],
                    city=address_data['city'],
                    state=address_data['state'],
                    country=address_data['country'],
                    is_saved_address=True,
                )
                selected_address = new_address
            except IntegrityError:
                # Handle IntegrityError if another request created the same address simultaneously
                selected_address = Address.objects.get(
                    user=current_user,
                    address_line_1=address_data['address_line_1'],
                    city=address_data['city'],
                    state=address_data['state'],
                    country=address_data['country'],
                )

    # Refresh saved_addresses to include the newly created address
    unique_addresses = Address.objects.filter(
        user=current_user, is_saved_address=True
    ).values('address_line_1', 'city', 'state', 'country').annotate(max_id=Max('id'))
    saved_addresses = Address.objects.filter(id__in=unique_addresses.values('max_id'))

    # Include selected_address in the context
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'cart_items': cart_items, 
        'variations': variations,
        'saved_addresses': saved_addresses,
        'selected_address': selected_address,
    }
    print(saved_addresses)
    return render(request, 'store/checkout.html', context)



def get_address_details(request):
    address_id = request.GET.get('address_id')
    address = Address.objects.get(id=address_id)

    data = {
        'first_name': address.first_name,
        'last_name': address.last_name,
        'email': address.email,
        'phone': address.phone,
        'address_line_1': address.address_line_1,
        'address_line_2': address.address_line_2,
        'city': address.city,
        'state': address.state,
        'country': address.country,
    }

    return JsonResponse(data)



from accounts.models import Address
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Q


def delete_address(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        
        # Ensure the user owns the address before deleting (optional)
        address = get_object_or_404(Address, id=address_id, user=request.user)

        # Get all addresses with the same values (modify the fields accordingly)
        addresses_to_delete = Address.objects.filter(
            Q(first_name=address.first_name) &
            Q(last_name=address.last_name) &
            Q(email=address.email) &
            Q(phone=address.phone) &
            Q(address_line_1=address.address_line_1) &
            Q(address_line_2=address.address_line_2) &
            Q(city=address.city) &
            Q(state=address.state) &
            Q(country=address.country)
        )

        # Perform the deletion
        addresses_to_delete.delete()
        
        print(f"All addresses with the same values as {address_id} deleted successfully")
        
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


