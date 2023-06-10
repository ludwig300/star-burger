import json

from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order, OrderItem, Product, Restaurant


def banners_list_api(request):
    # FIXME move data to db?
    return Response([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ])


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return Response(dumped_products)

@api_view(['POST'])
def register_order(request):
    data = request.data

    # create the order
    order = Order.objects.create(
        # restaurant=restaurant,
        first_name=data['firstname'],
        last_name=data['lastname'],
        phone_number=data['phonenumber'],
        address=data['address']
    )

    # create the order items
    for item in data['products']:
        product = Product.objects.get(pk=item['product'])
        order_item = OrderItem(
            order=order,
            product=product,
            quantity=item['quantity']
        )
        order_item.save()

    return Response({'success': True})
