from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

# ------------------------------
# Пользователь (расширение AbstractUser)
# ------------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'Пользователь'),
        ('owner', 'Владелец'),
        ('admin', 'Администратор'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name='Роль пользователя'
    )

    # ↓ Переопределяем groups для того,
    # чтобы не было конфликта с auth.User.groups
    groups = models.ManyToManyField(
        Group,
        verbose_name='Группы',
        blank=True,
        related_name='sait_user_set',     # уникальный related_name
        help_text='Группы, к которым принадлежит пользователь',
        related_query_name='user'
    )
    # ↓ Переопределяем user_permissions для того,
    # чтобы не было конфликта с auth.User.user_permissions
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='Права пользователя',
        blank=True,
        related_name='sait_user_permissions',  # уникальный related_name
        help_text='Права, которые есть у этого пользователя',
        related_query_name='user'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        # get_role_display() точно существует благодаря choices
        return f"{self.username} ({self.get_role_display()})"

    def get_role_display(self) -> str:
        """
        IDE иногда не «видит» динамический метод get_<field>_display() у CharField с choices.
        Поэтому дублируем через super() + # type: ignore, чтобы подавить предупреждение.
        """
        return super().get_role_display()  # type: ignore[attr-defined]


# ------------------------------
# Удобство (Amenity) — справочник
# ------------------------------
class Amenity(models.Model):
    name: str = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название удобства'
    )

    class Meta:
        verbose_name = 'Удобство'
        verbose_name_plural = 'Удобства'

    def __str__(self) -> str:
        return self.name


# ------------------------------
# Локация (Location) — площадка
# ------------------------------
class Location(models.Model):
    name: str = models.CharField(
        max_length=150,
        verbose_name='Название площадки'
    )
    address = models.TextField(
        verbose_name='Адрес'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание площадки'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='locations',       # у User появляется атрибут user.locations
        verbose_name='Владелец площадки'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Площадка'
        verbose_name_plural = 'Площадки'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name

    @property
    def room_count(self) -> int:
        """
        Подсчитывает количество связанных Room через related_name='rooms'.
        Добавляем # type: ignore[attr-defined], чтобы IDE не ругалась.
        """
        return self.rooms.count()  # type: ignore[attr-defined]
    room_count.fget.short_description = 'Количество комнат'


# ------------------------------
# Комната (Room)
# ------------------------------
class Room(models.Model):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='rooms',            # у Location появляется location.rooms
        verbose_name='Площадка'
    )
    name = models.CharField(
        max_length=150,
        verbose_name='Название комнаты'
    )
    capacity = models.PositiveIntegerField(
        verbose_name='Вместимость'
    )
    price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за час'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание комнаты'
    )
    amenities = models.ManyToManyField(
        Amenity,
        through='RoomAmenity',
        related_name='rooms',            # у Amenity появляется amenity.rooms
        verbose_name='Удобства'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления'
    )

    class Meta:
        verbose_name = 'Комната'
        verbose_name_plural = 'Комнаты'
        ordering = ['location', 'name']

    def __str__(self) -> str:
        return f"{self.name} ({self.location.name})"

    @property
    def amenities_list(self) -> str:
        """
        Формирует строку из связанных Amenity через .all().
        Добавляем # type: ignore[attr-defined], чтобы IDE не ругалась.
        """
        return ", ".join([a.name for a in self.amenities.all()])  # type: ignore[attr-defined]
    amenities_list.fget.short_description = 'Список удобств'


# ------------------------------
# Связующая таблица RoomAmenity (многие-ко-многим)
# ------------------------------
class RoomAmenity(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        verbose_name='Комната'
    )
    amenity = models.ForeignKey(
        Amenity,
        on_delete=models.CASCADE,
        verbose_name='Удобство'
    )

    class Meta:
        verbose_name = 'Удобство в комнате'
        verbose_name_plural = 'Удобства в комнатах'
        unique_together = ('room', 'amenity')
        ordering = ['room']

    def __str__(self) -> str:
        return f"{self.amenity.name} → {self.room.name}"


# ------------------------------
# Бронирование (Booking)
# ------------------------------
class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('canceled', 'Отменено'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',         # у User появляется user.bookings
        verbose_name='Пользователь'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='bookings',         # у Room появляется room.bookings
        verbose_name='Комната'
    )
    date = models.DateField(
        verbose_name='Дата бронирования'
    )
    start_time = models.TimeField(
        verbose_name='Время начала'
    )
    end_time = models.TimeField(
        verbose_name='Время окончания'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,           # get_status_display() будет корректно работать
        default='pending',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата изменения'
    )

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-date', 'start_time']
        get_latest_by = 'created_at'

    def __str__(self) -> str:
        # get_status_display() обозначается ниже для IDE
        return (
            f"Бронь: {self.room.name} на {self.date} "
            f"({self.start_time}–{self.end_time}) – {self.get_status_display()}"
        )

    def get_status_display(self) -> str:
        """
        IDE не всегда видит динамический метод get_<field>_display(),
        поэтому дублируем через super() с # type: ignore[attr-defined].
        """
        return super().get_status_display()  # type: ignore[attr-defined]


# ------------------------------
# Избранное (Favorite)
# ------------------------------
class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',        # у User появляется user.favorites
        verbose_name='Пользователь'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='favorited_by',     # у Room появляется room.favorited_by
        verbose_name='Комната'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное пользователей'
        unique_together = ('user', 'room')
        ordering = ['-created_at']

    def __str__(self) -> str:
        # self.user.username распознаётся IDE благодаря TYPE_CHECKING-импорту
        return f"{self.user.username} → {self.room.name}"  # type: ignore[attr-defined]


# ------------------------------
# Изображения комнат (Image)
# ------------------------------
class Image(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='images',           # у Room появляется room.images
        verbose_name='Комната'
    )
    url = models.URLField(
        verbose_name='URL изображения'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата загрузки'
    )

    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'
        ordering = ['-uploaded_at']

    def __str__(self) -> str:
        return f"Image ({self.id}) для {self.room.name}"  # type: ignore[attr-defined]


# ------------------------------
# Отзывы (Review)
# ------------------------------
class Review(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',           # у User появляется user.reviews
        verbose_name='Пользователь'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='reviews',           # у Room появляется room.reviews
        verbose_name='Комната'
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name='Рейтинг'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self) -> str:
        # self.user.username и self.room.name «видны» IDE через TYPE_CHECKING
        return f"{self.rating}★ от {self.user.username} для {self.room.name}"  # type: ignore[attr-defined]
