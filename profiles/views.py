from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Profile, Agent, Role, Ability, Team, Map, AbilityTemplate, UserRiot
from .forms import ProfileForm, SignupForm, RiotInfoForm


def get_user_profile(user):
    """Safely fetch the user's profile or return None without raising DoesNotExist."""
    if not user.is_authenticated:
        return None
    try:
        return user.profile
    except Profile.DoesNotExist:
        return None

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Stash riot info to prefill when creating/claiming a profile
            riot_id_val = form.cleaned_data.get('riot_id')
            riot_tag_val = form.cleaned_data.get('riot_tag')
            request.session['prefill_riot_id'] = riot_id_val
            request.session['prefill_riot_tag'] = riot_tag_val
            UserRiot.objects.create(user=user, riot_id=riot_id_val, riot_tag=riot_tag_val)
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('profile_list')
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def riot_info(request):
    """Allow a logged-in user to set or update their Riot ID/Tag used for claiming."""
    user_riot, _ = UserRiot.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = RiotInfoForm(request.POST)
        if form.is_valid():
            user_riot.riot_id = form.cleaned_data['riot_id']
            user_riot.riot_tag = form.cleaned_data['riot_tag']
            user_riot.save()
            request.session['prefill_riot_id'] = user_riot.riot_id
            request.session['prefill_riot_tag'] = user_riot.riot_tag
            messages.success(request, 'Riot info saved. You can now claim a profile.')
            return redirect('profile_list')
    else:
        form = RiotInfoForm(initial={
            'riot_id': user_riot.riot_id,
            'riot_tag': user_riot.riot_tag,
        })

    return render(request, 'profiles/riot_info.html', {'form': form})

def get_ability_rows(profile=None):
    """Helper to prepare ability rows for the template."""
    templates = AbilityTemplate.objects.all()
    existing_map = {}
    if profile:
        existing_map = {a.template.id: a for a in profile.abilities.all() if a.template}
    
    rows = []
    for t in templates:
        rows.append({
            'template': t,
            'ability': existing_map.get(t.id)
        })
    return rows


@login_required
def input_profile(request):
    """Form page to input all profile data."""
    if not request.user.is_authenticated:
        return redirect('login')

    # Restrict to one profile per user
    existing_profile = get_user_profile(request.user)
    if existing_profile:
        messages.info(request, "You already have a profile. You can edit it instead.")
        return redirect('display_profile', profile_id=existing_profile.id)
    # Prepare variables for persisting selection on potential error
    selected_agent_ids = []
    selected_role_ids = []
    selected_map_ids = []

    initial_data = {}
    # Prefill from session (saved at signup)
    if request.session.get('prefill_riot_id'):
        initial_data['riot_id'] = request.session.get('prefill_riot_id')
    if request.session.get('prefill_riot_tag'):
        initial_data['riot_tag'] = request.session.get('prefill_riot_tag')

    # Fallback to stored riot info on the user
    if not initial_data and hasattr(request.user, 'riot_info') and request.user.riot_info:
        initial_data['riot_id'] = request.user.riot_info.riot_id
        if request.user.riot_info.riot_tag:
            initial_data['riot_tag'] = request.user.riot_info.riot_tag

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES)
        
        # If POST, we might need these later if validation fails
        if request.POST.getlist('agent_id'):
            selected_agent_ids = [int(id) for id in request.POST.getlist('agent_id')]
        if request.POST.getlist('role_id'):
            selected_role_ids = [int(id) for id in request.POST.getlist('role_id')]
        if request.POST.getlist('map_id'):
            selected_map_ids = [int(id) for id in request.POST.getlist('map_id')]

        if profile_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()
            
            # Save selected agents (ManyToMany)
            agent_ids = request.POST.getlist('agent_id')
            if agent_ids:
                profile.agents.set(agent_ids)
            
            # Save selected roles (ManyToMany)
            role_ids = request.POST.getlist('role_id')
            if role_ids:
                profile.roles.set(role_ids)

            # Save selected maps (ManyToMany)
            map_ids = request.POST.getlist('map_id')
            if map_ids:
                if len(map_ids) > 3:
                    messages.warning(request, "You can select up to 3 maps. Only the first 3 were saved.")
                    map_ids = map_ids[:3] # Slice to keep only first 3
                profile.maps.set(map_ids)
            
            # Save abilities (linked to templates)
            for template in AbilityTemplate.objects.all():
                # Form fields expected to be named by template ID
                ability_name = request.POST.get(f'ability_name_{template.id}')
                ability_description = request.POST.get(f'ability_description_{template.id}')
                
                if ability_name and ability_description:
                    Ability.objects.create(
                        profile=profile,
                        template=template,
                        ability_name=ability_name,
                        ability_description=ability_description
                    )
            
            messages.success(request, 'Profile created successfully!')
            return redirect('display_profile', profile_id=profile.id)
    else:
        profile_form = ProfileForm(initial=initial_data)

    # Clear prefill after rendering once
    request.session.pop('prefill_riot_id', None)
    request.session.pop('prefill_riot_tag', None)
    
    return render(request, 'profiles/input_form.html', {
        'profile_form': profile_form,
        'available_agents': Agent.objects.select_related('role').all(),
        'available_roles': Role.objects.all(),
        'available_teams': Team.objects.all(),
        'available_maps': Map.objects.all(),
        'ability_rows': get_ability_rows(),
        'selected_agent_ids': selected_agent_ids,
        'selected_role_ids': selected_role_ids,
        'selected_map_ids': selected_map_ids,
    })


def display_profile(request, profile_id):
    """Display page showing all profile data."""
    profile = get_object_or_404(Profile, id=profile_id)
    
    # Find teammates (profiles with same team, excluding self)
    teammates = []
    if profile.team:
        teammates = Profile.objects.filter(team=profile.team).exclude(id=profile.id)
    
    context = {
        'profile': profile,
        'agents': profile.agents.all(),
        'roles': profile.roles.all(),
        'abilities': profile.abilities.all(),
        'teammates': teammates,
    }
    
    return render(request, 'profiles/display_profile.html', context)


def profile_list(request):
    """List all profiles."""
    profiles = Profile.objects.all()
    return render(request, 'profiles/profile_list.html', {'profiles': profiles})


@login_required
def account_overview(request):
    claimed_profile = get_user_profile(request.user)
    try:
        riot_info = request.user.riot_info
    except UserRiot.DoesNotExist:
        riot_info = None

    return render(request, 'profiles/account_overview.html', {
        'claimed_profile': claimed_profile,
        'riot_info': riot_info,
    })


@login_required
def edit_profile(request, profile_id):
    """Edit an existing profile."""
    profile = get_object_or_404(Profile, id=profile_id)

    # Ownership check
    if not request.user.is_authenticated or profile.user != request.user:
        messages.error(request, "You do not have permission to edit this profile.")
        return redirect('display_profile', profile_id=profile_id)
    
    # Prepare variables for persisting selection on potential error
    selected_agent_ids = []
    selected_role_ids = []
    selected_map_ids = []
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        # Capture selections from POST
        if request.POST.getlist('agent_id'):
            selected_agent_ids = [int(id) for id in request.POST.getlist('agent_id')]
        if request.POST.getlist('role_id'):
            selected_role_ids = [int(id) for id in request.POST.getlist('role_id')]
        if request.POST.getlist('map_id'):
            selected_map_ids = [int(id) for id in request.POST.getlist('map_id')]

        if profile_form.is_valid():
            profile = profile_form.save()
            
            # Update ManyToMany relationships
            agent_ids = request.POST.getlist('agent_id')
            profile.agents.set(agent_ids if agent_ids else [])
            
            role_ids = request.POST.getlist('role_id')
            profile.roles.set(role_ids if role_ids else [])

            map_ids = request.POST.getlist('map_id')
            if map_ids and len(map_ids) > 3:
                 messages.warning(request, "You can select up to 3 maps. Selection was truncated.")
                 map_ids = map_ids[:3]
            profile.maps.set(map_ids if map_ids else [])
            
            # Delete and recreate abilities
            profile.abilities.all().delete()
            
            for template in AbilityTemplate.objects.all():
                ability_name = request.POST.get(f'ability_name_{template.id}')
                ability_description = request.POST.get(f'ability_description_{template.id}')
                
                if ability_name and ability_description:
                    Ability.objects.create(
                        profile=profile,
                        template=template,
                        ability_name=ability_name,
                        ability_description=ability_description
                    )
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('display_profile', profile_id=profile.id)
    else:
        profile_form = ProfileForm(instance=profile)
        # Pre-fill selected IDs from DB
        selected_agent_ids = list(profile.agents.values_list('id', flat=True))
        selected_role_ids = list(profile.roles.values_list('id', flat=True))
        selected_map_ids = list(profile.maps.values_list('id', flat=True))
    
    # Get existing data for pre-filling the form
    context = {
        'profile_form': profile_form,
        'profile': profile,
        'agents': profile.agents.all(),
        'roles': profile.roles.all(),
        'abilities': profile.abilities.all(),
        'is_edit': True,
        'available_agents': Agent.objects.select_related('role').all(),
        'available_roles': Role.objects.all(),
        'available_teams': Team.objects.all(),
        'available_maps': Map.objects.all(),
        'ability_rows': get_ability_rows(profile),
        'selected_agent_ids': selected_agent_ids,
        'selected_role_ids': selected_role_ids,
        'selected_map_ids': selected_map_ids,
        'custom_errors': {},
    }
    
    return render(request, 'profiles/input_form.html', context)


def card_profile(request, profile_id):
    """Display the profile as a stylized card."""
    profile = get_object_or_404(Profile, id=profile_id)
    
    teammates = None
    if profile.team:
        teammates = Profile.objects.filter(team=profile.team).exclude(id=profile.id)

    return render(request, 'profiles/card_profile.html', {
        'profile': profile,
        'agents': profile.agents.all(),
        'roles': profile.roles.all(),
        'abilities': profile.abilities.all(),
        'teammates': teammates
    })


@login_required
def claim_profile(request, profile_id):
    """Allow a logged-in user without a profile to claim an unassociated profile via Riot ID/Tag verification."""
    profile = get_object_or_404(Profile, id=profile_id)

    # Block if the profile is already owned
    if profile.user:
        messages.error(request, "This profile is already claimed.")
        return redirect('display_profile', profile_id=profile_id)

    # Block if the current user already has a profile
    user_profile = get_user_profile(request.user)
    if user_profile:
        messages.info(request, "You already have a profile and cannot claim another.")
        return redirect('display_profile', profile_id=user_profile.id)

    try:
        user_riot = request.user.riot_info
    except UserRiot.DoesNotExist:
        user_riot = None
    if not user_riot:
        messages.error(request, "You need to set your Riot ID/Tag before claiming.")
        print(f"[CLAIM] user={request.user.username} missing riot_info")
        return redirect('riot_info')

    # Verify match
    def matches(profile_obj, riot_info):
        if (riot_info.riot_id or '').lower() != (profile_obj.riot_id or '').lower():
            return False
        profile_tag = profile_obj.riot_tag or ''
        user_tag = riot_info.riot_tag or ''
        return profile_tag.lower() == user_tag.lower()

    if request.method == 'POST':
        if matches(profile, user_riot):
            profile.user = request.user
            profile.save(update_fields=['user'])
            print(f"[CLAIM] user={request.user.username} claimed profile_id={profile.id} riot={profile.riot_id}{profile.riot_tag or ''}")
            messages.success(request, 'Profile claimed successfully!')
            return redirect('display_profile', profile_id=profile.id)
        else:
            print(f"[CLAIM-FAILED] user={request.user.username} riot={user_riot.riot_id}{user_riot.riot_tag or ''} target={profile.riot_id}{profile.riot_tag or ''}")
            messages.error(request, 'Your account Riot ID/Tag does not match this profile.')

    return render(request, 'profiles/claim_profile.html', {'profile': profile})


@login_required
def delete_profile(request, profile_id):
    """Delete a profile."""
    profile = get_object_or_404(Profile, id=profile_id)

    if profile.user != request.user:
        messages.error(request, "You do not have permission to delete this profile.")
        return redirect('display_profile', profile_id=profile_id)

    if request.method == 'POST':
        profile.delete()
        messages.success(request, f'Profile "{profile.in_game_name}" has been deleted successfully!')
        return redirect('profile_list')
    
    return redirect('display_profile', profile_id=profile_id)
