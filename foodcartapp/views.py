from rest_framework import status
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

    # validate input data
    if not all(key in data for key in [
        'firstname',
        'lastname',
        'phonenumber',
        'address',
        'products'
    ]):
        return Response(
            {'error': 'Missing required fields'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not isinstance(data['products'], list) or not data['products']:
        return Response(
            {'error': 'Invalid products: expected a non-empty list'},
            status=status.HTTP_400_BAD_REQUEST
        )

    for item in data['products']:
        if not isinstance(item, dict) or 'product' not in item or 'quantity' not in item:
            return Response(
                {'error': 'Invalid product data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            item['quantity'] = int(item['quantity'])
        except ValueError:
            return Response(
                {'error': 'Invalid quantity: expected an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if item['quantity'] <= 0:
            return Response(
                {'error': 'Invalid quantity: must be greater than 0'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # create the order
    try:
        order = Order.objects.create(
            first_name=data['firstname'],
            last_name=data['lastname'],
            phone_number=data['phonenumber'],
            address=data['address']
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # create the order items
    for item in data['products']:
        try:
            product = Product.objects.get(pk=item['product'])
            order_item = OrderItem(
                order=order,
                product=product,
                quantity=item['quantity']
            )
            order_item.save()
        except Product.DoesNotExist:
            return Response(
                {'error': 'Invalid product id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return Response({'success': True}, status=status.HTTP_200_OK)