from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [

    path('', views.index),

    path('admin/', admin.site.urls),

    path('signup/', views.signup),
    path('signup.html', views.signup),

    path('signin/', views.signin),
    path('signin.html', views.signin),

    path('login.html', views.signin),

    path('handle_signup/', views.handle_signup),

    path('add_restaurant.html', views.add_restaurant, name='add_restaurant'),

    path(
        'open_add_restaurant/',
        views.open_add_restaurant,
        name='open_add_restaurant'
    ),

    path(
        'show_restaurants/',
        views.open_show_restaurants,
        name='show_restaurants'
    ),

    path(
        'update_restaurant/<int:restaurant_id>/',
        views.update_restaurant,
        name='update_restaurant'
    ),
    path('handle_update_restaurant/', views.handle_update_restaurant, name='handle_update_restaurant'),
    path('delete_restaurant/<int:restaurant_id>/', views.delete_restaurant, name='delete_restaurant'),
    
    # Menu Items
    path('add_menu_item/<int:restaurant_id>/', views.open_add_menu_item, name='open_add_menu_item'),
    path('handle_add_menu_item/', views.handle_add_menu_item, name='handle_add_menu_item'),
    path('show_menu/<int:restaurant_id>/', views.show_menu, name='show_menu'),
    path('delete_menu_item/<int:item_id>/', views.delete_menu_item, name='delete_menu_item'),
    
    # Cart and Orders
    path('add_to_cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('view_cart/', views.view_cart, name='view_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('place_order/', views.place_order, name='place_order'),
    path('verify_payment/', views.verify_payment, name='verify_payment'),
    path('my_orders/', views.my_orders, name='my_orders'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)