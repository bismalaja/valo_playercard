from django import forms
from .models import Profile, Ability

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['in_game_name', 'riot_id', 'riot_tag', 'profile_picture', 'profile_picture_url', 'team', 'bio']
        widgets = {
            'in_game_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your in-game name'}),
            'riot_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Riot ID Name (e.g. Tyloo)'}),
            'riot_tag': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tag (e.g. #NA1)'}),
            'team': forms.Select(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'profile_picture_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional: Paste image URL'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        in_game_name = cleaned_data.get('in_game_name')
        riot_id = cleaned_data.get('riot_id')
        riot_tag = cleaned_data.get('riot_tag')

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


class AbilityForm(forms.ModelForm):
    class Meta:
        model = Ability
        fields = ['key_binding', 'ability_name', 'ability_description']
        widgets = {
            'key_binding': forms.Select(attrs={'class': 'form-control'}),
            'ability_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ability name'}),
            'ability_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe this ability...'}),
        }
