import os

from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User


# ============================================
# REFERENCE DATA MODELS (Admin manages these)
# ============================================

class Role(models.Model):
    """
    Valorant roles that exist independently.
    Examples: Duelist, Controller, Initiator, Sentinel
    Managed via Django admin.
    """
    name = models.CharField(max_length=50, unique=True)
    icon = models.ImageField(upload_to='roles/', blank=True, null=True)
    icon_url = models.URLField(max_length=500, blank=True, null=True, help_text='Alternative: Provide image URL instead of upload')
    
    def get_icon_url(self):
        """Returns icon URL - verifies uploaded file exists before returning its URL"""
        if self.icon:
            try:
                if os.path.exists(self.icon.path):
                    return self.icon.url
            except (ValueError, NotImplementedError):
                pass
        return self.icon_url or ''
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']  # Alphabetical ordering


class Agent(models.Model):
    """
    Valorant agents with their assigned role.
    Examples: Jett (Duelist), Brimstone (Controller)
    Agents MUST have a role assigned.
    Managed via Django admin.
    """
    name = models.CharField(max_length=50, unique=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)  # Agents require a role
    icon = models.ImageField(upload_to='agents/', blank=True, null=True)
    icon_url = models.URLField(max_length=500, blank=True, null=True, help_text='Alternative: Provide image URL instead of upload')
    
    def get_icon_url(self):
        """Returns icon URL - verifies uploaded file exists before returning its URL"""
        if self.icon:
            try:
                if os.path.exists(self.icon.path):
                    return self.icon.url
            except (ValueError, NotImplementedError):
                pass
        return self.icon_url or ''
    
    def __str__(self):
        return f"{self.name} ({self.role.name})"
    
    class Meta:
        ordering = ['name']  # Alphabetical ordering


class Team(models.Model):
    """
    Predefined teams that players can select.
    Managed via Django admin.
    """
    name = models.CharField(max_length=100, unique=True)
    icon = models.ImageField(upload_to='teams/', blank=True, null=True)
    icon_url = models.URLField(max_length=500, blank=True, null=True, help_text='Alternative: Provide image URL instead of upload')
    custom_order = models.PositiveIntegerField(default=0, help_text="Higher numbers appear later in the list")
    
    def get_icon_url(self):
        """Returns icon URL - verifies uploaded file exists before returning its URL"""
        if self.icon:
            try:
                if os.path.exists(self.icon.path):
                    return self.icon.url
            except (ValueError, NotImplementedError):
                pass
        return self.icon_url or ''
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['custom_order', 'name']


class Map(models.Model):
    """
    Valorant maps.
    Managed via Django admin.
    """
    name = models.CharField(max_length=50, unique=True)
    icon = models.ImageField(upload_to='maps/', blank=True, null=True)
    icon_url = models.URLField(max_length=500, blank=True, null=True, help_text='Alternative: Provide image URL instead of upload')
    
    def get_icon_url(self):
        """Returns icon URL - verifies uploaded file exists before returning its URL"""
        if self.icon:
            try:
                if os.path.exists(self.icon.path):
                    return self.icon.url
            except (ValueError, NotImplementedError):
                pass
        return self.icon_url or ''
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


# ============================================
# AUTH EXTENSION MODEL
# ============================================

class UserProfile(models.Model):
    """
    Extends the built-in User with a Riot ID so we can match
    accounts to existing (unclaimed) profiles.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    riot_id = models.CharField(
        max_length=50,
        default='',
        help_text="Your Riot ID name (e.g. 'Tyloo')"
    )
    riot_tag = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^#[a-zA-Z0-9]{2,5}$',
                message='Tag must start with # and be followed by 2-5 alphanumeric characters (e.g. #NA1)'
            )
        ],
        help_text="Tag starting with # followed by 2-5 characters"
    )

    def __str__(self):
        return f"{self.user.username} ({self.riot_id}{self.riot_tag or ''})"


# ============================================
# USER PROFILE MODEL
# ============================================

class Profile(models.Model):
    """
    Player profile with basic info and selections.
    Users select from pre-existing agents, roles, and teams.
    """
    in_game_name = models.CharField(max_length=100)
    riot_id = models.CharField(max_length=50, default='', help_text="Your Riot ID name (e.g. 'Tyloo')")
    riot_tag = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^#[a-zA-Z0-9]{2,5}$',
                message='Tag must start with # and be followed by 2-5 alphanumeric characters (e.g. #NA1, #12345)'
            )
        ],
        help_text="Tag starting with # followed by 2-5 characters"
    )
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    profile_picture_url = models.URLField(max_length=500, blank=True, null=True, help_text='Alternative: Provide image URL instead of upload')
    team = models.ForeignKey(Team, on_delete=models.PROTECT, null=True, blank=True)
    
    peak_rank = models.CharField(max_length=100, blank=True, default='')

    # ManyToMany: Users can select multiple agents they play
    agents = models.ManyToManyField(Agent, blank=True, related_name='player_profiles')
    
    # ManyToMany: Users can select multiple roles they play
    roles = models.ManyToManyField(Role, blank=True, related_name='player_profiles')
    
    # ManyToMany: Users can select favorite maps
    maps = models.ManyToManyField(Map, blank=True, related_name='player_profiles')

    bio = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Ownership — null means this is an unclaimed legacy profile
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profile'
    )

    @property
    def is_claimed(self):
        return self.user is not None

    def get_profile_picture_url(self):
        """Returns profile picture URL - either from upload or external link"""
        if self.profile_picture:
            return self.profile_picture.url
        return self.profile_picture_url or ''

    def __str__(self):
        return self.in_game_name

    class Meta:
        ordering = ['-created_at']



