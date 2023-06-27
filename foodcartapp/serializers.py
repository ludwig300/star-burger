from django.db import transaction
from rest_framework.serializers import ModelSerializer, ValidationError
from .models import GeocodeData, Order, OrderItem


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(
        many=True,
        allow_empty=False,
        write_only=True
    )

    class Meta:
        model = Order
        fields = [
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'products'
        ]

    @transaction.atomic
    def create(self, validated_data):
        products_data = validated_data.pop('products')

        lat, lon = GeocodeData.objects.fetch_coordinates(validated_data['address'])
        if lat is None or lon is None:
            raise ValidationError("Could not determine the coordinates for the given address.")

        validated_data['latitude'] = lat
        validated_data['longitude'] = lon

        order = Order.objects.create(**validated_data)
        for product_data in products_data:
            product = product_data['product']
            OrderItem.objects.create(
                order=order,
                price=product.price,
                **product_data
            )
        return order


class ReadOrderSerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address']