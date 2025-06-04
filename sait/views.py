from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Count
from .models import Room, Booking, Location
from django.contrib.auth import login
from .forms import SignUpForm
def home(request):
    # 1) Топ популярных комнат (Room) по количеству бронирований:
    popular_places = (
        Room.objects
        .annotate(num_bookings=Count('bookings'))  # related_name='bookings' в модели Booking
        .order_by('-num_bookings')[:5]
    )

    # 2) Ближайшие бронирования (Booking):
    upcoming_bookings = (
        Booking.objects
        .filter(date__gte=timezone.now().date())
        .order_by('date')[:5]
    )

    # 3) Список всех площадок (Location) для селекта поиска:
    locations = Location.objects.all()

    return render(request, 'home.html', {
        'popular_places': popular_places,
        'upcoming_bookings': upcoming_bookings,
        'locations': locations,
    })
def search_results(request):
    location_id = request.GET.get('location')
    date_str = request.GET.get('date')

    rooms = Room.objects.filter(is_active=True)

    if location_id:
        rooms = rooms.filter(location__id=location_id)

    if date_str:
        booked_rooms = Booking.objects.filter(date=date_str).values_list('room_id', flat=True)
        rooms = rooms.exclude(id__in=booked_rooms)

    return render(request, 'search_results.html', {
        'rooms': rooms
    })

def places_list(request):
    rooms = Room.objects.filter(is_active=True).order_by('name')
    return render(request, 'places_list.html', {'rooms': rooms})

def booking_list(request):
    bookings = Booking.objects.select_related('room').order_by('-date')
    return render(request, 'booking_list.html', {'bookings': bookings})
def create_booking(request):
    if request.method == 'POST':
        room_id = request.POST.get('room')
        date_str = request.POST.get('date')
        user = request.user  # или request.POST.get('user_name'), если нет User

        # Проверка: нет ли уже брони на эту комнату/дату
        if Booking.objects.filter(room_id=room_id, date=date_str).exists():
            error = "Эта комната уже забронирована на выбранную дату."
            return render(request, 'error.html', {'error': error})

        # Получаем объект Room
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            error = "Комнаты с таким ID не существует."
            return render(request, 'error.html', {'error': error})

        # Создаём бронь (используем user.username, если у вас User)
        Booking.objects.create(room=room, date=date_str, user=user)
        return redirect('booking_success')

    return render(request, 'create_booking.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # сразу авторизуем
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})
