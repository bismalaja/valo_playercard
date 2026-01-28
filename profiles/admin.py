from django.contrib import admin
from .models import Profile, Agent, Role, Ability, Team, Map, AbilityTemplate


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


@admin.register(AbilityTemplate)
class AbilityTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'key_binding', 'icon']
    list_filter = ['key_binding']
    search_fields = ['name']


class AbilityInline(admin.TabularInline):
    model = Ability
    extra = 1


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['in_game_name', 'team', 'created_at']
    search_fields = ['in_game_name', 'team__name']
    list_filter = ['team', 'created_at']
    filter_horizontal = ['agents', 'roles', 'maps']  # Nice UI for ManyToMany
    inlines = [AbilityInline]


@admin.register(Ability)
class AbilityAdmin(admin.ModelAdmin):
    list_display = ['ability_name', 'get_template_key', 'profile']
    list_filter = ['profile', 'template__key_binding']

    def get_template_key(self, obj):
        return obj.template.key_binding if obj.template else '-'
    get_template_key.short_description = 'Key'
