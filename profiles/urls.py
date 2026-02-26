from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_list, name='profile_list'),
    path('signup/', views.signup, name='signup'),
    path('account/riot/', views.riot_info, name='riot_info'),
    path('account/', views.account_overview, name='account_overview'),
    path('create/', views.input_profile, name='input_profile'),
    path('profile/<int:profile_id>/', views.display_profile, name='display_profile'),
    path('profile/<int:profile_id>/card/', views.card_profile, name='card_profile'),
    path('profile/<int:profile_id>/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<int:profile_id>/delete/', views.delete_profile, name='delete_profile'),
    path('profile/<int:profile_id>/claim/', views.claim_profile, name='claim_profile'),
]
