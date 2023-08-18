from audioop import reverse

from django.contrib.auth import logout, authenticate, login, user_logged_in, user_logged_out
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.dispatch import receiver
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from pyexpat.errors import messages

from .forms import CustomUserCreationForm, CustomAuthenticationForm, EditProfileForm, MessageForm
from .models import UserProfile, Message, CustomUser, Friend


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)  # Создать экземпляр UserProfile
            login(request, user)
            return redirect('base')  # Перенаправить на вашу главную страницу
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/registration.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('base')  # Перенаправьте на вашу главную страницу
    else:
        form = CustomAuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def edit_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('base')
    else:
        form = EditProfileForm(instance=user_profile)

    return render(request, 'edit_profile.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def chat_view(request, recipient_id):
    recipient = get_object_or_404(User, id=recipient_id)
    recipient_profile = recipient.userprofile
    recipient_profile.is_online = True
    recipient_profile.save()

    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=recipient)) |
        (Q(sender=recipient) & Q(recipient=request.user))
    ).order_by('timestamp')

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.save()
            return redirect('chat_view', recipient_id=recipient_id)
        else:
            print(form.errors)  # Вывод ошибок формы в консоль для отладки

    return render(request, 'chat_view.html', {'recipient': recipient, 'messages': messages, 'form': form})


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    user_profile = UserProfile.objects.get_or_create(user=user)[0]
    user_profile.is_online = True
    user_profile.save()

@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    user_profile = UserProfile.objects.get_or_create(user=user)[0]
    user_profile.is_online = False
    user_profile.save()

def add_friend(request, user_id):
    friend = get_object_or_404(CustomUser, id=user_id)
    Friend.objects.get_or_create(from_user=request.user, to_user=friend)
    friends = Friend.objects.filter(from_user=request.user)
    return render(request, 'friends.html', {'friends': friends})

@login_required
def friends(request):
    user_profile = UserProfile.objects.get(user=request.user)
    friends_list = user_profile.friends.all()
    return render(request, 'friends.html', {'friends_list': friends_list})

def users_list(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    users = CustomUser.objects.exclude(id=request.user.id)
    success_message = request.GET.get('success_message')

    friend_ids = Friend.objects.filter(from_user=request.user).values_list('to_user', flat=True)
    friends = CustomUser.objects.filter(id__in=friend_ids)

    if request.method == 'POST':
        friend_username = request.POST.get('friend_username')
        friend = CustomUser.objects.filter(username=friend_username).first()

        if friend:
            Friend.objects.get_or_create(from_user=request.user, to_user=friend)
            messages.success(request, f'You are now friends with {friend.username}.')
            return redirect('users_list')

        messages.error(request, 'User not found or you cannot add yourself as a friend.')

    return render(request, 'users_list.html', {'user_profile': user_profile, 'users': users, 'success_message': success_message, 'friends': friends})





def base(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'base.html', {'user_profile': user_profile})



def about(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'about.html', {'user_profile': user_profile})

def contact(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'contact.html', {'user_profile': user_profile})

def home(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'home.html', {'user_profile': user_profile})

