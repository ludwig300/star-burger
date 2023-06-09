import json

from django.http import JsonResponse
from django.templatetags.static import static

from .models import Product, Order, OrderItem, Restaurant


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
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
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


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
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def register_order(request):
    try:
        data = json.loads(request.body.decode())
    except ValueError:
        return JsonResponse({
            'error': 'Invalid JSON',
        }, status=400)
    print(data)
    # try:
    #     restaurant = Restaurant.objects.get(pk=data['restaurant_id'])
    # except Restaurant.DoesNotExist:
    #     return JsonResponse({
    #         'error': 'Restaurant does not exist',
    #     }, status=400)

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

    return JsonResponse({'success': True})
