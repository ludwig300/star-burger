import copy
import json
import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Prefetch, Sum
from django.utils import timezone
from geopy.distance import geodesic
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from phonenumber_field.modelfields import PhoneNumberField

logging.basicConfig(filename='log.txt', filemode='a', level=logging.INFO)

logger = logging.getLogger(__name__)


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=400,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def with_total_price(self):
        return self.annotate(
            total_price=Sum(
                F('order_items__price') * F('order_items__quantity')
            )
        )
    def get_not_done_orders_with_total_price(self):
        return self.with_total_price().exclude(status='DONE')

    def get_orders_with_restaurants(self, restaurants):
        for order in self:
            order_location = (order.longitude, order.latitude)
            order.restaurants = []
            for restaurant in restaurants:
                restaurant_location = (restaurant.longitude, restaurant.latitude)
                restaurant_copy = copy.deepcopy(restaurant)
                if restaurant_location is not None and order_location is not None:
                    try:
                        restaurant_copy.distance = geodesic(
                            restaurant_location, order_location).km
                    except GeocoderTimedOut:
                        restaurant_copy.distance = None
                        logger.error(
                            "GeocoderTimedOut occurred, setting distance to None"
                        )
                    except GeocoderServiceError:
                        restaurant_copy.distance = None
                        logger.error(
                            "GeocoderServiceError occurred, setting distance to None"
                        )
                else:
                    restaurant_copy.distance = None
                order.restaurants.append(restaurant_copy)
            order.restaurants = sorted(
                order.restaurants, key=lambda r: r.distance if r.distance is not None else float('inf'))
        return self



class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        ELECTRONIC = 'E', 'Электронно'
        CASH = 'C', 'Наличными'
        NOT_INDICATED = 'N', 'Не указано'

    STATUS_CHOICES = [
        ('NEW', 'Новый заказ'),
        ('CONFIRMED', 'Подтверждён'),
        ('IN_PROGRESS', 'В процессе'),
        ('DONE', 'Выполнен'),
    ]

    payment_method = models.CharField(
        'способ оплаты',
        max_length=1,
        choices=PaymentMethod.choices,
        default=PaymentMethod.NOT_INDICATED,
        db_index=True
    )
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default='NEW',
        db_index=True
    )
    firstname = models.CharField(
        'имя',
        max_length=50
    )
    lastname = models.CharField(
        'фамилия',
        max_length=50
    )
    phonenumber = PhoneNumberField(
        'номер телефона',
        max_length=20
    )
    address = models.CharField(
        'адрес',
        max_length=250
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    objects = OrderQuerySet.as_manager()
    date_registration = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )
    called_at = models.DateTimeField(blank=True, null=True, db_index=True)
    delivered_at = models.DateTimeField(blank=True, null=True, db_index=True)
    assigned_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Назначенный ресторан',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    comment = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def items_list(self, obj):
        return ", ".join([str(item) for item in obj.items.all()])
    items_list.short_description = 'Items'

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.address}"

    @property
    def suitable_restaurants(self):
        suitable_restaurants = []
        restaurants = Restaurant.objects.prefetch_related(
            Prefetch('menu_items', queryset=RestaurantMenuItem.objects.filter(
                availability=True))
        )
        order_products = self.items.all()

        for restaurant in restaurants:
            menu_products = [
                item.product for item in restaurant.menu_items.all()
            ]
            if set(order_products).issubset(menu_products):
                suitable_restaurants.append(restaurant)

        return suitable_restaurants


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        verbose_name='заказ',
        related_name='order_items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='продукт',
        related_name='ordered_items'
    )
    quantity = models.IntegerField(
        'количество',
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'пункт меню заказа'
        verbose_name_plural = 'пункты меню заказа'

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"


class GeocodeDataManager(models.Manager):

    def fetch_coordinates(self, address):
        one_week_ago = timezone.now() - timedelta(weeks=1)
        geodata = self.filter(
            address=address, updated_at__gte=one_week_ago).first()

        if geodata is not None:
            return geodata.latitude, geodata.longitude

        try:
            base_url = "https://geocode-maps.yandex.ru/1.x"
            response = requests.get(base_url, params={
                "geocode": address,
                "apikey": settings.YANDEX_API_KEY,
                "format": "json",
            })
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Problem with request: {e}")
            return None

        try:
            found_places = response.json()['response']['GeoObjectCollection']['featureMember']
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Problem parsing response JSON: {e}")
            return None

        if not found_places:
            return None
        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        self.create(address=address, latitude=lat, longitude=lon)
        return lat, lon


class GeocodeData(models.Model):
    address = models.CharField(max_length=255, unique=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GeocodeDataManager()
