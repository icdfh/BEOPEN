from audioop import reverse
from os import path

from django.contrib.auth import logout, authenticate, login, user_logged_in, user_logged_out
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.dispatch import receiver
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from pyexpat.errors import messages
from django.contrib import messages
import openai
from django.utils.translation import gettext as _

from . import admin
from .forms import CustomUserCreationForm, CustomAuthenticationForm, EditProfileForm, MessageForm, PostForm, VideoForm, \
    ChatForm
from .models import UserProfile, Message, CustomUser, Friend, News, Post, Video
import logging
from openpyxl import Workbook
from django.contrib.auth.decorators import user_passes_test




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


@login_required
def add_friend(request):
    users = CustomUser.objects.exclude(id=request.user.id)
    user_profile = UserProfile.objects.get(user=request.user)

    # Получите список ID друзей текущего пользователя
    friend_ids = user_profile.friends.values_list('user_id', flat=True)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        friend_profile = get_object_or_404(UserProfile, id=user_id)

        if friend_profile.user == request.user:
            messages.error(request, "You can't add yourself as a friend.")
            return redirect('add_friend')

        if friend_profile in user_profile.friends.all():
            messages.error(request, f'{friend_profile.user.username} is already your friend.')
            return redirect('add_friend')

        user_profile.friends.add(friend_profile)
        friend_profile.friends.add(user_profile)

        messages.success(request, f'You are now friends with {friend_profile.user.username}.')
        return redirect('add_friend')

    return render(request, 'add_friend.html', {'users': users, 'friend_ids': friend_ids, 'user_profile': user_profile})


@login_required
def remove_friend(request, friend_id):
    friend_to_remove = get_object_or_404(UserProfile, id=friend_id)
    user_profile = request.user.userprofile

    # Удалите друга из списка друзей текущего пользователя
    user_profile.friends.remove(friend_to_remove)

    return redirect('friends')


@login_required
def friends(request):
    user_profile = UserProfile.objects.get(user=request.user)
    friends_list = user_profile.friends.all()
    return render(request, 'friends.html', {'friends_list': friends_list, 'user_profile': user_profile})

def posts(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('news')
    else:
        form = PostForm()
    return render(request, 'posts.html', {'form': form, 'user_profile': user_profile})

def video(request):
    videos = Video.objects.all()
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = VideoForm(request.POST)
        if form.is_valid():
            video = form.save(commit=False)
            video.author = request.user
            video.save()
            return redirect('video')
    else:
        form = VideoForm()

    return render(request, 'video.html', {'videos': videos, 'user_profile': user_profile, 'form': form})

def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Проверка, что текущий пользователь является автором поста
    if post.author == request.user:
        post.delete()
        return redirect('posts')  # Перенаправить на страницу со списком постов
    else:
        # Вернуть ошибку, если текущий пользователь не является автором
        return render(request, 'error.html', {'error_message': 'You do not have permission to delete this post.'})

@login_required
def delete_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    # Проверка, что текущий пользователь является автором видео
    if video.author == request.user:
        video.delete()
        return redirect('video')  # Перенаправить на страницу со списком видео
    else:
        # Вернуть ошибку, если текущий пользователь не является автором
        return render(request, 'error.html', {'error_message': 'You do not have permission to delete this video.'})



def base(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'base.html', {'user_profile': user_profile})


def news(request):
    news_list = News.objects.all()
    posts = Post.objects.all()
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    paginator = Paginator(news_list, 2)
    page = request.GET.get('page')
    news_list = paginator.get_page(page)
    return render(request, 'news.html' ,{ 'news_list': news_list, 'user_profile': user_profile, 'posts': posts})

def news_detail(request, pk):
    news_item = get_object_or_404(News, pk=pk)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'news_detail.html', {'news_item': news_item, 'user_profile': user_profile})


def chat_with_gpt(request):
    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            user_message = form.cleaned_data['user_message']

            # Отправка запроса к GPT-3 API
            openai.api_key = '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'
            response = openai.Completion.create(
                engine="davinci",
                prompt=user_message,
                max_tokens=50  # Максимальное количество токенов в ответе
            )
            assistant_response = response.choices[0].text.strip()

            return render(request, 'help.html', {'user_message': user_message, 'assistant_response': assistant_response})
    else:
        form = ChatForm()

    return render(request, 'help.html', {'form': form})



def export_to_excel(request):
    # Создайте рабочую книгу и лист
    wb = Workbook()
    ws = wb.active

    # Добавьте заголовки
    ws.append(["Имя", "Email"])

    # Добавьте данные (замените этот блок кода на вашу логику получения данных)
    data = [
        ["John Doe", "john@example.com"],
        ["Jane Smith", "jane@example.com"],
    ]
    for row in data:
        ws.append(row)

    # Создайте HTTP-ответ с содержимым XLSX
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=mydata.xlsx'

    # Сохраните рабочую книгу в HTTP-ответ
    wb.save(response)

    return response


def search(request):
    query = request.GET.get('q')  # Получите строку поиска из запроса GET

    # Выполните поиск по моделям, которые вам интересны
    posts = Post.objects.filter(title__icontains=query)
    videos = Video.objects.filter(title__icontains=query)

    # Здесь можно добавить другие модели для поиска, если необходимо

    return render(request, 'search_results.html', {'posts': posts, 'videos': videos, 'query': query})

def search_results(request):
    query = request.GET.get('q')  # Получите строку поиска из запроса GET

    # Выполните поиск по моделям, которые вам интересны
    posts = Post.objects.filter(title__icontains=query)
    videos = Video.objects.filter(title__icontains=query)

    # Здесь можно добавить другие модели для поиска, если необходимо

    return render(request, 'search_result.html', {'posts': posts, 'videos': videos, 'query': query})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'post_detail.html', {'post': post})

def my_view(request):
    translated_text = _("Hello, World!")
    return render(request, 'my_template.html', {'translated_text': translated_text})


def is_editor(user):
    return user.role == 'editor'


@login_required
def add_balance(request, user_id):
    # Проверка, что текущий пользователь является редактором
    if not request.user.role == 'editor':
        return redirect('base')  # Перенаправить на главную страницу или другую страницу по вашему выбору

    user_to_update = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')  # Получить сумму для пополнения
        try:
            amount = float(amount)
            if amount > 0:
                user_to_update.userprofile.balance += amount
                user_to_update.userprofile.save()
                messages.success(request, f'Баланс пользователя {user_to_update.username} успешно пополнен.')
                return redirect('base')
            else:
                messages.error(request, 'Сумма должна быть больше нуля.')
        except ValueError:
            messages.error(request, 'Некорректная сумма.')

    return render(request, 'add_balance.html', {'user_to_update': user_to_update})

def about(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'about.html', {'user_profile': user_profile})

def contact(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'contact.html', {'user_profile': user_profile})

def home(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'home.html', {'user_profile': user_profile})

