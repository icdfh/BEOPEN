from django.conf.urls.static import static
from django.urls import path
from . import views
from django.conf import settings

from .views import add_friend, chat_with_gpt

urlpatterns = [
    path('', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('base/', views.base, name='base'),
    path('home/', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('news/', views.news, name='news'),
    path('news/<int:pk>/', views.news_detail, name='news_detail'),
    path('posts/', views.posts, name='posts'),
    path('delete_post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('video/', views.video, name='video'),
    path('delete_video/<int:video_id>/', views.delete_video, name='delete_video'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('logout/', views.logout_view, name='logout'),
    path('add_friend/', views.add_friend, name='add_friend'),
    path('remove_friend/<int:friend_id>/', views.remove_friend, name='remove_friend'),
    path('friends/', views.friends, name='friends'),
    path('help/', views.chat_with_gpt, name='chat_with_gpt'),
    path('export/', views.export_to_excel, name='export_to_excel'),
    path('search/', views.search, name='search'),
    path('search_results/', views.search_results, name='search_results'),
    path('post/<int:pk>/', views.post_detail, name='post_detail')


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)