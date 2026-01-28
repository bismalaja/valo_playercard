from django.contrib import admin
from .models import Profile, Agent, Role, Ability, Team


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


class AbilityInline(admin.TabularInline):
    model = Ability
    extra = 1


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['in_game_name', 'team', 'created_at']
    search_fields = ['in_game_name', 'team__name']
    list_filter = ['team', 'created_at']
    filter_horizontal = ['agents', 'roles']  # Nice UI for ManyToMany
    inlines = [AbilityInline]


@admin.register(Ability)
class AbilityAdmin(admin.ModelAdmin):
    list_display = ['ability_name', 'key_binding', 'profile', 'order']
    list_filter = ['profile', 'key_binding']
