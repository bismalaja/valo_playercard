from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_list, name='profile_list'),
    path('create/', views.input_profile, name='input_profile'),
    path('profile/<int:profile_id>/', views.display_profile, name='display_profile'),
    path('profile/<int:profile_id>/card/', views.card_profile, name='card_profile'),
    path('profile/<int:profile_id>/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<int:profile_id>/delete/', views.delete_profile, name='delete_profile'),
]
