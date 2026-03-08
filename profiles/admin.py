from django.contrib import admin
from .models import Profile, Agent, Role, Team, Map, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'riot_id', 'riot_tag']
    search_fields = ['user__username', 'riot_id']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'icon']
    search_fields = ['name']
    list_filter = ['role']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'custom_order', 'icon']
    list_editable = ['custom_order']
    search_fields = ['name']
    ordering = ['custom_order', 'name']


@admin.register(Map)
class MapAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['in_game_name', 'team', 'user', 'is_claimed', 'created_at']
    search_fields = ['in_game_name', 'team__name']
    list_filter = ['team', 'created_at']
    filter_horizontal = ['agents', 'roles', 'maps']  # Nice UI for ManyToMany

    def is_claimed(self, obj):
        return obj.is_claimed
    is_claimed.boolean = True
