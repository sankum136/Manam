from django.shortcuts import render, get_object_or_404, redirect 

from django.http import HttpResponse
from delivery.models import Customer, Restaurant, MenuItem, CartItem, Order, OrderItem
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


def index(request):
    return render(request, 'index.html')

def signup(request):
    return render(request, 'signup.html')

def signin(request):
    
    if request.method == 'POST':
        
        username = request.POST['username']
        password = request.POST['password']
        
        if username == 'admin' and password == 'admin':
            request.session['is_admin'] = True
            return render(request, 'admin.html')
            
        try:
            customer = Customer.objects.get(username=username, password=password)
            request.session['customer_id'] = customer.id
            request.session['is_admin'] = False
            restaurantList = Restaurant.objects.all()
            return render(request, 'customer_home.html', {'customer': customer, 'restaurantList': restaurantList})
            
        except Customer.DoesNotExist:
            return render(request, 'fail.html', {'message': 'Invalid Username or Password'})
      
    return render(request, 'signin.html')


def open_add_restaurant(request):
    return render (request, 'add_restaurant.html')


def handle_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not username or not email or not password:
            return render(request, 'fail.html', {'message': 'All fields are required'})
        
        try:
            Customer.objects.get(username=username)
            return render(request, 'fail.html', {'message': 'Username already exists'})
        except Customer.DoesNotExist:
            Customer.objects.create(username=username, email=email, password=password)
            return render(request, 'signin.html', {'message': 'Account created successfully! Please sign in.'})
    else:
        return HttpResponse("Please use POST method")

def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        rating = request.POST['rating']
        image = request.POST['image']

        try:
            Restaurant.objects.get(name=name)
            return HttpResponse('Duplicate restaurant')
        except Restaurant.DoesNotExist:
            Restaurant.objects.create(name=name, 
            description=description, 
            rating=rating,  
            image=image)
            
            
        return render(request, 'admin.html')

    return render(request, 'add_restaurant.html')

def open_show_restaurants(request):
    
    restaurantList = Restaurant.objects.all()

    return render(
        request,
        'show_restaurant.html',

        {'restaurantList': restaurantList}
    )

def update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    return render(request, 'update_restaurant.html', {'restaurant': restaurant})

def handle_update_restaurant(request):
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant_id')
        name = request.POST.get('restaurant_name')
        description = request.POST.get('restaurant_description')
        rating = request.POST.get('restaurant_rating')
        image = request.POST.get('restaurant_image')

        restaurant = Restaurant.objects.get(id=restaurant_id)
        restaurant.name = name
        restaurant.description = description
        restaurant.rating = rating
        restaurant.image = image
        restaurant.save()

        return render(request, 'admin.html')
    return HttpResponse("Invalid request method")

def delete_restaurant(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
        restaurant.delete()
    except Restaurant.DoesNotExist:
        pass
    return open_show_restaurants(request)

# Menu Item Views
def open_add_menu_item(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(request, 'add_menu_item.html', {'restaurant': restaurant})

def handle_add_menu_item(request):
    if request.method == 'POST':
        restaurant_id = request.POST.get('restaurant_id')
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.POST.get('image')

        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        MenuItem.objects.create(
            restaurant=restaurant,
            name=name,
            description=description,
            price=price,
            image=image
        )
        return show_menu(request, restaurant_id)
    return HttpResponse("Invalid request")

def show_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    menu_items = restaurant.menu_items.all()
    is_admin = request.GET.get('admin') == 'true' or request.session.get('is_admin', False)
    return render(request, 'show_menu.html', {
        'restaurant': restaurant,
        'menu_items': menu_items,
        'is_admin': is_admin
    })

def delete_menu_item(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    restaurant_id = item.restaurant.id
    item.delete()
    return show_menu(request, restaurant_id)

# Cart and Order Views
def add_to_cart(request, item_id):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('/signin/')
    
    customer = get_object_or_404(Customer, id=customer_id)
    item = get_object_or_404(MenuItem, id=item_id)
    
    cart_item, created = CartItem.objects.get_or_create(customer=customer, menu_item=item)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return redirect(f'/show_menu/{item.restaurant.id}/')

def view_cart(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('/signin/')
    
    customer = get_object_or_404(Customer, id=customer_id)
    cart_items = CartItem.objects.filter(customer=customer)
    total = sum(item.menu_item.price * item.quantity for item in cart_items)
    
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total, 'customer': customer})

def remove_from_cart(request, item_id):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('/signin/')
    
    cart_item = get_object_or_404(CartItem, id=item_id, customer_id=customer_id)
    cart_item.delete()
    return redirect('/view_cart/')

def place_order(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('/signin/')
    
    customer = get_object_or_404(Customer, id=customer_id)
    cart_items = CartItem.objects.filter(customer=customer)
    
    if not cart_items:
        return redirect('/show_restaurants/')
    
    total = sum(item.menu_item.price * item.quantity for item in cart_items)
    order = Order.objects.create(customer=customer, total_price=total)
    
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            menu_item=item.menu_item,
            quantity=item.quantity,
            price=item.menu_item.price
        )
    
    
    # Razorpay Integration
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Amount is in paise (1 INR = 100 paise)
        razorpay_order = client.order.create({
            'amount': int(total * 100),
            'currency': 'INR',
            'payment_capture': '1'
        })
        
        order.razorpay_order_id = razorpay_order['id']
        order.save()
        
        razorpay_order_id = razorpay_order['id']
        razorpay_amount = razorpay_order['amount']
    except Exception as e:
        # Fallback for demo/invalid keys
        if 'Authentication failed' in str(e) or 'rzp_test_YOUR_KEY_ID' in settings.RAZORPAY_KEY_ID:
            # Create a mock order ID for demonstration if keys are placeholders
            razorpay_order_id = f"order_mock_{order.id}"
            razorpay_amount = int(total * 100)
            order.razorpay_order_id = razorpay_order_id
            order.save()
        else:
            return render(request, 'fail.html', {'message': f'Razorpay Error: {str(e)}'})
    
    context = {
        'order': order,
        'customer': customer,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'razorpay_amount': razorpay_amount,
        'currency': 'INR',
        'callback_url': '/verify_payment/'
    }
    
    return render(request, 'payment.html', context)


@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            if not razorpay_order_id.startswith('order_mock_'):
                client.utility.verify_payment_signature(params_dict)
                
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            order.status = 'Paid'
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.save()

            
            # Clear cart after successful payment verification
            CartItem.objects.filter(customer=order.customer).delete()
            
            return render(request, 'order_success.html', {'order': order, 'customer': order.customer})
        except Exception as e:
            return render(request, 'fail.html', {'message': 'Payment verification failed'})
            
    return HttpResponse("Invalid request")


def my_orders(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('/signin/')
    
    customer = get_object_or_404(Customer, id=customer_id)
    orders = Order.objects.filter(customer=customer).order_by('-order_date')
    return render(request, 'orders.html', {'orders': orders, 'customer': customer})