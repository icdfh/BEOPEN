from django.conf.urls.static import static
from django.urls import path
from . import views
from django.conf import settings

urlpatterns = [
    path('', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('base/', views.base, name='base'),
    path('home/', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('chat/<int:recipient_id>/', views.chat_view, name='chat_view'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('logout/', views.logout_view, name='logout'),
    path('chat/<int:recipient_id>/add_friend/', views.add_friend, name='add_friend'),
    path('friends/', views.friends, name='friends'),
    path('users_list/', views.users_list, name='users_list'),
    path('add_friend/<int:user_id>/', views.add_friend, name='add_friend'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)