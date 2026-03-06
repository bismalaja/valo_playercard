from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_list, name='profile_list'),
    path('create/', views.input_profile, name='input_profile'),
    path('profile/<int:profile_id>/', views.display_profile, name='display_profile'),
    path('profile/<int:profile_id>/card/', views.card_profile, name='card_profile'),
    path('profile/<int:profile_id>/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<int:profile_id>/delete/', views.delete_profile, name='delete_profile'),
    path('profile/<int:profile_id>/claim/', views.claim_profile_view, name='claim_profile'),
    # Auth
    path('accounts/signup/', views.signup_view, name='signup_view'),
    path('accounts/login/', views.login_view, name='login_view'),
    path('accounts/logout/', views.logout_view, name='logout_view'),
    path('accounts/unclaim/', views.unclaim_profile_view, name='unclaim_profile'),
]
