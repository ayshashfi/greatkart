from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
from django.template.loader import render_to_string
import datetime
import json
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from datetime import datetime, date           
from orders.models import Notification
import datetime

@login_required(login_url='admin_login')
def order_list(request):
    if not request.user.is_superadmin:
        return redirect('admin_login')
    
    orders = Order.objects.all().order_by('-created_at')
    ordered_product = OrderProduct.objects.all().order_by('-created_at')
    paginator = Paginator(orders, 7)
    page_number = request.GET.get('page')
    order_page = paginator.get_page(page_number)
    page_nums = range(1, order_page.paginator.num_pages + 1)
    notifications = Notification.objects.all().order_by('-timestamp')[:5]
    today_notifications = [notification for notification in notifications if notification.timestamp.date() == date.today()]
    
    return render(request, 'admin/order.html', {'orders': orders, 'ordered_product':ordered_product,'order_page': order_page, 'page_nums': page_nums,'notifications':notifications,'today_notifications':today_notifications})





def payments(request):
    
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Store transaction details inside Payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()
    
    # Move the cart items to Order Product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.product_price
        orderproduct.ordered = True
        orderproduct.save()
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()
        print("variations:",product_variation)
        for variation in item.variations.all():
            variation.quantity -= item.quantity
            variation.save()
        

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order recieved email to customer
    mail_subject = 'Thank you for your order!'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Send order number and transaction id back to sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)



    
from accounts.models import Address

def place_order(request, total=0, quantity=0):
    current_user = request.user

    # If the cart count is less than or equal to 0, then redirect back to the store
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0

    for cart_item in cart_items:
        # Check if the product has an offer
        if cart_item.product.offer:
            # Calculate the discounted price for the current item
            discounted_price = cart_item.product.product_price - cart_item.product.offer.discount_amount
            cart_item.discounted_price = discounted_price
            cart_item.save()
            # Add the discounted price to the total
            total += (discounted_price * cart_item.quantity)
        else:
            # If there is no offer, use the regular product price for the total
            total += (cart_item.product.product_price * cart_item.quantity)

        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            billing_address = Address.objects.create(
                            user=current_user,
                            first_name=form.cleaned_data['first_name'],
                            last_name=form.cleaned_data['last_name'],
                            phone=form.cleaned_data['phone'],
                            email=form.cleaned_data['email'],
                            address_line_1=form.cleaned_data['address_line_1'],
                            address_line_2=form.cleaned_data['address_line_2'],
                            country=form.cleaned_data['country'],
                            state=form.cleaned_data['state'],
                            city=form.cleaned_data['city'],
                            order_note=form.cleaned_data['order_note'],
                            is_saved_address=True,
)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'billing_address':billing_address,
            }
            
            return render(request, 'orders/payments.html', context)
    return redirect('checkout')
    
    

def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        payment_method="PayPal"
        subtotal = 0
        
        
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)
        
          # Calculate the discounted subtotal
        subtotal = sum(
            (item.product.product_price - (item.product.offer.discount_amount if item.product.offer else 0)) * item.quantity
            for item in ordered_products
        )

        # Calculate the total discount amount
        total_discount_amount = sum(
            (item.product.offer.discount_amount if item.product.offer else 0) * item.quantity
            for item in ordered_products
        )

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
            'payment_method':payment_method,
            'total_discount_amount':total_discount_amount,
            
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
    


def update_order_status(request, order_id):
    if not request.user.is_superadmin:
        return redirect('admin_login')

    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')

        # Validate the new status against allowed choices
        if new_status in dict(Order.STATUS).keys():
            order.status = new_status
            order.save()
            messages.success(request, 'Order status updated successfully.')
        else:
            messages.error(request, 'Invalid order status.')

    return redirect('order_list')




def cancel_order(request, order_id):
    # Get the order object
    order = get_object_or_404(Order, id=order_id)

    # Add your cancellation logic here
    order.status = 'Cancelled'
    order.save()

    return redirect('my_orders')


from .forms import ReturnItemForm

def return_item(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        form = ReturnItemForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            item_name = form.cleaned_data['item_name']
            
            # Create a ReturnedItem object
            returned_item = ReturnedItem.objects.create(
                order=order,
                user=request.user,
                item_name=item_name,
                reason=reason
            )

            # Update the order status or perform other actions as needed
            order.status = 'Returned'
            order.save()

            # Redirect to a success page or return a success response
            return render(request, 'orders/order_return_success.html', {'returned_item': returned_item})

    else:
        form = ReturnItemForm()

    return render(request, 'orders/return_item.html', {'form': form, 'order': order})




from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ReturnedItem, Notification

@receiver(post_save, sender=ReturnedItem)
def create_returned_item_notification(sender, instance, created, **kwargs):
    if created:
        message = f"New return item for order #{instance.order.id}: {instance.item_name}"
        Notification.objects.create(message=message)




def view_order_details(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'orders/view_order_details.html', {'order': order})



import logging

logger = logging.getLogger(__name__)

def cod(request,order_number):
    current_user = request.user
    
    try:
        order = Order.objects.get(user=current_user, is_ordered=False,id=order_number)

        order.status = 'New'
        order.is_ordered = True
        order.save()

        # Move the cart item into the order product table
        cart_items = CartItem.objects.filter(user=current_user)
        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.product_price
            orderproduct.ordered = True
            orderproduct.save()

            cart_item = CartItem.objects.get(id=item.id)

            product_variation = cart_item.variations.all()
            orderproduct = OrderProduct.objects.get(id=orderproduct.id)
            orderproduct.variations.set(product_variation)
            orderproduct.save()

            for variation in item.variations.all():
                variation.quantity -= item.quantity
                variation.save()

        # Clear the cart
        CartItem.objects.filter(user=request.user).delete()

        # Send the order received email to the customer
        mail_subject = "Thank you for your order"
        message = render_to_string('orders/order_recieved_email.html', {
            'user': request.user,
            'order': order,
        })
        to_email = request.user.email
        send_email = EmailMessage(mail_subject, message, to=[to_email])
        send_email.send()

        order_number = order.order_number
        request.session['order_number'] = order_number
        return redirect('cod_order_complete', order_number=order.id,)

    except Order.DoesNotExist:
        logger.error(f"Order not found for Order ID: {order_number}, Current User: {current_user}")
        raise




def cod_order_complete(request, order_number):
    current_user = request.user

    try:
        order = Order.objects.get(user=current_user, id=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        payment_method = "Cash On Delivery"

        # Calculate the discounted subtotal
        subtotal = sum(
            (item.product.product_price - (item.product.offer.discount_amount if item.product.offer else 0)) * item.quantity
            for item in ordered_products
        )

        # Calculate the total discount amount
        total_discount_amount = sum(
            (item.product.offer.discount_amount if item.product.offer else 0) * item.quantity
            for item in ordered_products
        )

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'subtotal': subtotal,
            'total_discount_amount': total_discount_amount,
            'payment_method': payment_method,
        }
        return render(request, 'orders/cod_complete.html', context)

    except Order.DoesNotExist:
        logger.error(f"Order not found for Order Number: {order_number}")
        raise







from django.shortcuts import get_object_or_404, render
from io import BytesIO
from reportlab.pdfgen import canvas

def download_invoice_paypal(request, order_number):
    # Retrieve the order
    order = get_object_or_404(Order, order_number=order_number)
    ordered_products = OrderProduct.objects.filter(order_id=order.id)
    payment_method = "PayPal"
    subtotal = sum(item.product_price * item.quantity for item in ordered_products)
    
    total_discount_amount = sum(
        (item.product.offer.discount_amount if item.product.offer else 0) * item.quantity
        for item in ordered_products
    )

    # Create a BytesIO buffer to store the PDF
    buffer = BytesIO()

    # Create the PDF object, using the BytesIO buffer as its "file."
    pdf = canvas.Canvas(buffer)

    # Set the font for the PDF
    pdf.setFont("Helvetica", 12)

    # Add a heading
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(100, 800, "GreatKart Invoice")

    # Add a subheading
    pdf.setFont("Helvetica", 14)
    pdf.drawString(100, 780, f"Invoice for Order #{order.order_number}")

    # Add a box around the order details
    pdf.rect(80, 740, 450, 200)

    # Starting y-position for content inside the box
    y_position = 720

    # Invoiced To
    pdf.drawString(100, y_position, "Invoiced To:")
    y_position -= 15
    pdf.drawString(120, y_position, f"{order.first_name} {order.last_name}")
    y_position -= 15
    pdf.drawString(120, y_position, f"{order.address_line_1}")
    y_position -= 15
    if order.address_line_2:
        pdf.drawString(120, y_position, f"{order.address_line_2}")
        y_position -= 15
    pdf.drawString(120, y_position, f"{order.city}, {order.state}")
    y_position -= 15
    pdf.drawString(120, y_position, f"{order.country}")
    y_position -= 15
    pdf.drawString(120, y_position, f"Phone: {order.phone}")
    y_position -= 15
    pdf.drawString(120, y_position, f"Email: {order.email}")
    y_position -= 30

    # Draw a line after invoiced to details
    pdf.line(100, y_position, 530, y_position)
    y_position -= 30

    # Order Details
    pdf.drawString(100, y_position, "Order Details:")
    y_position -= 15
    pdf.drawString(120, y_position, f"Order: #{order_number}")
    y_position -= 15
    pdf.drawString(120, y_position, f"Transaction ID: {order.payment}")
    y_position -= 15
    pdf.drawString(120, y_position, f"Order Date: {order.created_at}")
    y_position -= 15
    pdf.drawString(120, y_position, f"Payment Status: {order.payment.status}")
    y_position -= 15
    pdf.drawString(120, y_position, f"Payment Method: {payment_method}")
    y_position -= 30
    # Draw a line after order details
    pdf.line(100, y_position, 530, y_position)
    y_position -= 30

    # Ordered Products
    pdf.drawString(100, y_position, "Ordered Products:")
    y_position -= 15

    for item in ordered_products:
        product_info = f"{item.product.product_name} - {item.quantity} x ${item.product_price} = ${item.product_price * item.quantity}"
        pdf.drawString(120, y_position, product_info)
        y_position -= 15

    # Draw a line after ordered products
    pdf.line(100, y_position, 530, y_position)
    y_position -= 10

    # Total Box
   
   
    pdf.drawString(100, y_position -40, f"Subtotal: ${subtotal}")
    pdf.drawString(100, y_position - 60, f"Discount: ${total_discount_amount}")
    pdf.drawString(100, y_position - 80, f"Tax: ${order.tax}")
    pdf.drawString(100, y_position-100, f"Grand Total: ${order.order_total}")

    y_position -= 30

    # Thank you message
    pdf.drawString(100, y_position-100, "Thank you for shopping with us!")

    # Save the PDF to the buffer
    pdf.showPage()
    pdf.save()

    # Set the buffer's position to the beginning
    buffer.seek(0)

    # Create a response object with the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=invoice_{order_number}.pdf'
    response.write(buffer.read())

    return response




def download_invoice_cod(request, order_number):
    # Retrieve the order
    order = get_object_or_404(Order, order_number=order_number)
    ordered_products = OrderProduct.objects.filter(order_id=order.id)
    payment_method = "Cash On Delivery"
    subtotal = sum(item.product_price * item.quantity for item in ordered_products)
    
    total_discount_amount = sum(
        (item.product.offer.discount_amount if item.product.offer else 0) * item.quantity
        for item in ordered_products
    )

    # Create a BytesIO buffer to store the PDF
    buffer = BytesIO()

    # Create the PDF object, using the BytesIO buffer as its "file."
    pdf = canvas.Canvas(buffer)

    # Set the font for the PDF
    pdf.setFont("Helvetica", 12)

    # Add a heading
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(100, 800, "GreatKart Invoice")

    # Add a subheading
    pdf.setFont("Helvetica", 14)
    pdf.drawString(100, 780, f"Invoice for Order #{order.order_number}")

    # Add a box around the order details
    pdf.rect(80, 740, 450, 200)

    # Starting y-position for content inside the box
    y_position = 720

    # Invoiced To
    pdf.drawString(100, y_position, "Invoiced To:")
    y_position -= 15
    pdf.drawString(120, y_position, f"{order.first_name} {order.last_name}")
    y_position -= 15
    pdf.drawString(120, y_position, f"{order.address_line_1}")
    y_position -= 15
    if order.address_line_2:
        pdf.drawString(120, y_position, f"{order.address_line_2}")
        y_position -= 15
    pdf.drawString(120, y_position, f"{order.city}, {order.state}")
    y_position -= 15
    pdf.drawString(120, y_position, f"{order.country}")
    y_position -= 15
    pdf.drawString(120, y_position, f"Phone: {order.phone}")
    y_position -= 15
    pdf.drawString(120, y_position, f"Email: {order.email}")
    y_position -= 30

    # Draw a line after invoiced to details
    pdf.line(100, y_position, 530, y_position)
    y_position -= 30

    # Order Details
    pdf.drawString(100, y_position, "Order Details:")
    y_position -= 15
    pdf.drawString(120, y_position, f"Order: #{order_number}")
    y_position -= 15
    pdf.drawString(120, y_position, f"Order Date: {order.created_at}")
    y_position -= 15
    pdf.drawString(120, y_position, f"Payment Method: {payment_method}")
    y_position -= 30
    # Draw a line after order details
    pdf.line(100, y_position, 530, y_position)
    y_position -= 30

    # Ordered Products
    pdf.drawString(100, y_position, "Ordered Products:")
    y_position -= 15

    for item in ordered_products:
        product_info = f"{item.product.product_name} - {item.quantity} x ${item.product_price} = ${item.product_price * item.quantity}"
        pdf.drawString(120, y_position, product_info)
        y_position -= 15

    # Draw a line after ordered products
    pdf.line(100, y_position, 530, y_position)
    y_position -= 10

    # Total Box
   
   
    pdf.drawString(100, y_position -40, f"Subtotal: ${subtotal}")
    pdf.drawString(100, y_position - 60, f"Discount: ${total_discount_amount}")
    pdf.drawString(100, y_position - 80, f"Tax: ${order.tax}")
    pdf.drawString(100, y_position-100, f"Grand Total: ${order.order_total}")

    y_position -= 30

    # Thank you message
    pdf.drawString(100, y_position-100, "Thank you for shopping with us!")

    # Save the PDF to the buffer
    pdf.showPage()
    pdf.save()

    # Set the buffer's position to the beginning
    buffer.seek(0)

    # Create a response object with the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=invoice_{order_number}.pdf'
    response.write(buffer.read())

    return response