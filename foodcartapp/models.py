from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


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


class Order(models.Model):
    # restaurant = models.ForeignKey(
    #     Restaurant,
    #     verbose_name='ресторан',
    #     related_name='orders',
    #     on_delete=models.CASCADE
    # )
    items = models.ManyToManyField(
        Product,
        through='OrderItem',
        verbose_name='товары'
    )
    first_name = models.CharField(
        'имя',
        max_length=50
    )
    last_name = models.CharField(
        'фамилия',
        max_length=50
    )
    phone_number = PhoneNumberField(
        'номер телефона',
        max_length=20
    )
    address = models.CharField(
        'адрес',
        max_length=250
    )

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def items_list(self, obj):
        return ", ".join([str(item) for item in obj.items.all()])
    items_list.short_description = 'Items'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.address}"


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

    class Meta:
        verbose_name = 'пункт меню заказа'
        verbose_name_plural = 'пункты меню заказа'

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
