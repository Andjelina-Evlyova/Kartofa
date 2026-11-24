from django.db import models
from django.core.validators import MinValueValidator


class SiteSettings(models.Model):
    brand_name = models.CharField("Име на бранда", max_length=80, default="КартофЪ")
    brand_location = models.CharField("Град / локация", max_length=80, default="Асеновград")
    phone = models.CharField("Телефон за поръчки", max_length=40, default="0879 255 509")
    order_notification_email = models.EmailField(
        "Имейл за известия за поръчки",
        blank=True,
        default="aevlyovva@gmail.com",
    )
    order_notification_phone = models.CharField(
        "Телефон за известия за поръчки",
        max_length=40,
        blank=True,
        default="0879 255 509",
    )
    address = models.CharField("Адрес", max_length=255, default='ул. „Цар Иван Асен II“ №95')
    second_address = models.CharField("Втори адрес", max_length=255, blank=True, default='бул. „България“ №60')
    hero_kicker = models.CharField("Надпис над hero заглавието", max_length=120, default="Приготвено с любов в Асеновград")
    hero_title = models.CharField("Hero заглавие", max_length=180, default="КартофЪ")
    hero_text = models.CharField("Hero подзаглавие", max_length=300, default="Избери своя любим картоф — приготвен точно по твой вкус.")
    hero_button_text = models.CharField("Текст на hero бутона", max_length=80, default="Виж пълнените картофи")
    hero_image = models.ImageField("Hero снимка", upload_to="site/", blank=True)
    menu_kicker = models.CharField("Надпис над менюто", max_length=120, default="Нашите специални")
    menu_title = models.CharField("Заглавие на менюто", max_length=120, default="ПРЕДЛОЖЕНИЯ")
    builder_kicker = models.CharField("Надпис над конструктора", max_length=120, default="Направи го твой")
    builder_title = models.CharField("Заглавие на конструктора", max_length=120, default="ТВОЯТ ПЪЛНЕН КАРТОФЪ")
    builder_text = models.TextField("Описание на конструктора", default="Избери броя добавки, основата и любимите си пълнежи.")
    about_title = models.CharField("Заглавие За нас", max_length=120, default="Вкусът, който се помни.")
    about_text = models.TextField("Текст За нас", default="КартофЪ в Асеновград предлага щедро пълнени печени картофи.")
    footer_text = models.TextField("Текст във футъра", default="Големи печени и пълнени картофи, сандвичи и комбо менюта.")
    weekday_hours = models.CharField("Работно време понеделник – петък", max_length=80, default="09:00 – 21:00")
    weekend_hours = models.CharField("Работно време събота – неделя", max_length=80, default="10:00 – 20:00")
    instagram_url = models.URLField("Instagram", blank=True)
    facebook_url = models.URLField("Facebook", blank=True)
    tiktok_url = models.URLField("TikTok", blank=True)
    copyright_text = models.CharField("Текст за авторски права", max_length=180, default="© 2026 КартофЪ. Всички права запазени.")

    class Meta:
        verbose_name = "Настройки на сайта"
        verbose_name_plural = "Настройки на сайта"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Настройки на уебсайта"


class BuilderSize(models.Model):
    name = models.CharField("Име", max_length=80)
    topping_count = models.PositiveIntegerField("Брой добавки", validators=[MinValueValidator(1)])
    price = models.DecimalField("Цена (€)", max_digits=8, decimal_places=2)
    sort_order = models.PositiveIntegerField("Ред", default=0)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        ordering = ["sort_order", "topping_count"]
        verbose_name = "Размер на картофа"
        verbose_name_plural = "Размери на картофа"

    def __str__(self):
        return f"{self.name} — {self.price} €"


class BuilderTopping(models.Model):
    name = models.CharField("Добавка", max_length=80)
    extra_price = models.DecimalField("Допълнителна цена (€)", max_digits=8, decimal_places=2, default=0)
    sort_order = models.PositiveIntegerField("Ред", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Пълнеж"
        verbose_name_plural = "Пълнежи"

    def __str__(self):
        return self.name


class MenuCollection(models.Model):
    name = models.CharField("Име на колекцията", max_length=100)
    slug = models.SlugField("Код за филтъра", max_length=100, unique=True)
    sort_order = models.PositiveIntegerField("Ред", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Колекция от менюто"
        verbose_name_plural = "Колекции от менюто"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("Име на продукта", max_length=120)
    collection = models.ForeignKey(
        MenuCollection,
        verbose_name="Колекция",
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField("Цена (€)", max_digits=8, decimal_places=2, null=True, blank=True)
    image = models.ImageField("Снимка на продукта", upload_to="products/", blank=True)
    is_available = models.BooleanField("Наличен", default=True)
    is_featured = models.BooleanField("Избран продукт", default=False)
    sort_order = models.PositiveIntegerField("Ред на показване", default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Продукт"
        verbose_name_plural = "Продукти"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).only("image").first()
            if previous and previous.image and previous.image != self.image:
                previous.image.delete(save=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

class Order(models.Model):
    DELIVERY = "delivery"
    PICKUP = "pickup"
    ORDER_TYPE_CHOICES = [
        (DELIVERY, "Доставка"),
        (PICKUP, "Лично взимане"),
    ]

    STATUS_CHOICES = [
        ("new", "Нова поръчка"),
        ("confirmed", "Потвърдена"),
        ("ready", "Готова"),
        ("completed", "Приключена"),
        ("cancelled", "Отказана"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="new")
    customer_name = models.CharField("Име и фамилия", max_length=120, blank=True)
    customer_phone = models.CharField("Телефон", max_length=30, blank=True)
    delivery_address = models.CharField("Адрес за доставка", max_length=255, blank=True)
    pickup_location = models.CharField("Обект за взимане", max_length=255, blank=True)
    ready_in_minutes = models.PositiveIntegerField("Готова след минути", null=True, blank=True)
    items = models.JSONField("Поръчани продукти", default=list)
    total = models.DecimalField("Обща сума (€)", max_digits=8, decimal_places=2)
    staff_note = models.CharField("Бележка към поръчката", max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Поръчка"
        verbose_name_plural = "Поръчки"

    def __str__(self):
        return f"Поръчка #{self.pk} · {self.get_order_type_display()} · {self.total} €"
