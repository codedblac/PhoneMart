from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import datetime
from .models import Product, CartItem, Payment, Order, Category
from .stk_push import initiate_stk_push
from .forms import UserRegistrationForm

def product_list(request):
    category_id = request.GET.get('category')
    products = Product.objects.all()
    categories = Category.objects.all()
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    return render(request, 'shop/product_list.html', {
        'products': products,
        'categories': categories
    })

@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity
    cart_item.save()
    messages.success(request, f'Added {quantity} {product.name} to cart')
    return redirect('cart')

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.get_total() for item in cart_items)
    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.get_total() for item in cart_items)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        shipping_address = request.POST.get('shipping_address')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        
        # Create pending payment
        payment = Payment.objects.create(
            user=request.user,
            amount=total,
            transaction_id=f"PENDING_{request.user.id}_{datetime.datetime.now().timestamp()}"
        )
        
        # Store shipping info in session
        request.session['shipping_info'] = {
            'address': shipping_address,
            'latitude': latitude,
            'longitude': longitude,
            'payment_id': payment.id
        }
        
        response = initiate_stk_push(phone_number, int(total))
        print(f"STK Push Response in View: {response}")  # Add logging
        if response.get('ResponseCode') == '0':
            messages.success(request, 'Payment initiated. Please complete on your phone.')
            return redirect('cart')
        else:
            messages.error(request, f'Payment initiation failed: {response.get("error", "Unknown error")}')
    
    return render(request, 'shop/checkout.html', {'total': total})

@login_required
def delete_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'shop/register.html', {'form': form})

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
        transaction_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
        
        payment = Payment.objects.get(transaction_id=transaction_id)
        if result_code == 0:
            payment.status = 'completed'
            payment.save()
            
            # Create order
            shipping_info = request.session.get('shipping_info', {})
            order = Order.objects.create(
                user=payment.user,
                payment=payment,
                shipping_address=shipping_info.get('address'),
                latitude=shipping_info.get('latitude'),
                longitude=shipping_info.get('longitude')
            )
            
            # Add items to order and clear cart
            cart_items = CartItem.objects.filter(user=payment.user)
            order.items.set(cart_items)
            cart_items.delete()
            
            messages.success(request, 'Payment successful! Your order has been dispatched.')
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, 'Payment failed. Please try again.')
            
    return JsonResponse({'status': 'received'})

def homepage(request):
    featured_products = Product.objects.all()[:6]  # Get first 6 products
    categories = Category.objects.all()
    return render(request, 'shop/home.html', {
        'featured_products': featured_products,
        'categories': categories
    })