from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Profile


# ---------------------------------------------------------------------------
# AUTH FORMS
# ---------------------------------------------------------------------------

class SignUpForm(UserCreationForm):
    riot_id = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Riot ID Name (e.g. Tyloo)',
        }),
        help_text='Your Riot ID name (without the #tag)',
    )
    riot_tag = forms.CharField(
        max_length=10,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^#[a-zA-Z0-9]{2,5}$',
                message='Tag must start with # followed by 2-5 alphanumeric characters (e.g. #NA1)',
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '#NA1',
        }),
        help_text='The # tag portion of your Riot ID (e.g. #NA1)',
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'riot_id', 'riot_tag']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password',
        })
        # Remove verbose default help texts
        self.fields['username'].help_text = 'Required. 150 characters or fewer.'
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters.'
        self.fields['password2'].help_text = 'Enter the same password again for verification.'


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
        })

class ProfileForm(forms.ModelForm):
    MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024
    ALLOWED_PROFILE_PICTURE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    ALLOWED_PROFILE_PICTURE_CONTENT_TYPES = {
        'image/jpeg',
        'image/png',
        'image/webp',
    }

    peak_rank_display = forms.CharField(
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Fetched from Tracker.gg',
            'readonly': True,
            'tabindex': '-1',
            'style': 'opacity: 0.55; cursor: not-allowed; pointer-events: none;',
        }),
    )

    remove_profile_picture = forms.BooleanField(
        required=False,
        label='Remove current profile picture',
    )

    class Meta:
        model = Profile
        fields = ['in_game_name', 'riot_id', 'riot_tag', 'profile_picture', 'profile_picture_url', 'team', 'bio']
        widgets = {
            'in_game_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your Username'}),
            'riot_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Riot ID Name (e.g. Tyloo)'}),
            'riot_tag': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tag (e.g. #NA1)'}),
            'team': forms.Select(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'profile_picture_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional: Paste image URL'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['peak_rank_display'].initial = (self.instance.peak_rank if self.instance and self.instance.pk else '')
        self.fields['remove_profile_picture'].widget.attrs.update({'class': 'remove-picture-checkbox'})
        self._new_profile_picture = self.files.get('profile_picture') if hasattr(self, 'files') else None

        # Hide remove checkbox when there's nothing to remove.
        if not self.instance.pk or not self.instance.get_profile_picture_url():
            self.fields['remove_profile_picture'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        in_game_name = cleaned_data.get('in_game_name')
        riot_id = cleaned_data.get('riot_id')
        riot_tag = cleaned_data.get('riot_tag')
        profile_picture_url = (cleaned_data.get('profile_picture_url') or '').strip()
        remove_profile_picture = bool(cleaned_data.get('remove_profile_picture'))

        has_new_upload = bool(self._new_profile_picture)
        cleaned_data['profile_picture_url'] = profile_picture_url

        if has_new_upload:
            upload = self._new_profile_picture
            ext = ''
            if upload.name and '.' in upload.name:
                ext = upload.name[upload.name.rfind('.'):].lower()

            if ext not in self.ALLOWED_PROFILE_PICTURE_EXTENSIONS:
                self.add_error(
                    'profile_picture',
                    'Only .jpg, .jpeg, .png, and .webp files are allowed.',
                )

            if upload.size > self.MAX_PROFILE_PICTURE_SIZE:
                self.add_error('profile_picture', 'Image must be 5MB or smaller.')

            content_type = getattr(upload, 'content_type', '') or ''
            if content_type and content_type not in self.ALLOWED_PROFILE_PICTURE_CONTENT_TYPES:
                self.add_error(
                    'profile_picture',
                    'Invalid image type. Use JPEG, PNG, or WebP.',
                )

        if profile_picture_url:
            allowed_prefixes = ('https://', 'http://', '/static/', '/media/')
            if not profile_picture_url.startswith(allowed_prefixes):
                self.add_error(
                    'profile_picture_url',
                    'Image URL must start with http://, https://, /static/, or /media/.',
                )

        # Keep image source singular to avoid hidden precedence bugs.
        # Priority: new upload > explicit remove > URL value.
        if has_new_upload:
            cleaned_data['profile_picture_url'] = ''
        elif remove_profile_picture:
            cleaned_data['profile_picture'] = None
            cleaned_data['profile_picture_url'] = ''
        elif profile_picture_url:
            cleaned_data['profile_picture'] = None

        # Check for duplicate duplicate in_game_name
        if in_game_name:
            # Case-insensitive check, excluding current profile if editing
            query = Profile.objects.filter(in_game_name__iexact=in_game_name)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                self.add_error('in_game_name', 'This In-Game Name is already taken.')

        # Check for duplicate Riot ID + Tag combination
        if riot_id:
            # If tag is empty, treat it as empty string for comparison
            tag_value = riot_tag if riot_tag else ''
            
            # Handle both NULL and empty string in DB for tag matching
            # Filter for same ID (case-insensitive)
            query = Profile.objects.filter(riot_id__iexact=riot_id)
            
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            
            # Since tag can be NULL or Empty in DB, we need to be careful.
            # We'll just check matches in Python to be safe given the complexity of NULL vs '' on different DBs
            # Or construct a complex Q object
            duplicates = False
            for p in query:
                db_tag = p.riot_tag if p.riot_tag else ''
                if db_tag.lower() == tag_value.lower():
                    duplicates = True
                    break
            
            if duplicates:
                error_msg = f"The Riot ID {riot_id}"
                if tag_value:
                    error_msg += f"{tag_value}"
                error_msg += " is already in use."
                
                self.add_error('riot_id', error_msg)
                if tag_value:
                    self.add_error('riot_tag', 'Combination taken.')

        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)

        remove_profile_picture = bool(self.cleaned_data.get('remove_profile_picture'))
        profile_picture_url = (self.cleaned_data.get('profile_picture_url') or '').strip()
        has_new_upload = bool(self._new_profile_picture)

        existing_upload = None
        if self.instance.pk and getattr(self.instance, 'profile_picture', None):
            existing_upload = self.instance.profile_picture

        # If switching to URL or explicit remove, clear old uploaded file first.
        if remove_profile_picture or profile_picture_url:
            if existing_upload:
                existing_upload.delete(save=False)
            profile.profile_picture = None

        if has_new_upload:
            profile.profile_picture = self._new_profile_picture
            profile.profile_picture_url = ''
        elif remove_profile_picture:
            profile.profile_picture = None
            profile.profile_picture_url = ''
        elif profile_picture_url:
            profile.profile_picture_url = profile_picture_url

        if commit:
            profile.save()
            self.save_m2m()
        return profile

