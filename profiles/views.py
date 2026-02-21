from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Profile, Agent, Role, Ability, Team, Map, AbilityTemplate
from .forms import ProfileForm

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


def input_profile(request):
    """Form page to input all profile data."""
    # Prepare variables for persisting selection on potential error
    selected_agent_ids = []
    selected_role_ids = []
    selected_map_ids = []

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
            profile = profile_form.save()
            
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
        profile_form = ProfileForm()
    
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


def edit_profile(request, profile_id):
    """Edit an existing profile."""
    profile = get_object_or_404(Profile, id=profile_id)
    
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
        'teammates': teammates
    })


def delete_profile(request, profile_id):
    """Delete a profile."""
    profile = get_object_or_404(Profile, id=profile_id)
    
    if request.method == 'POST':
        profile.delete()
        messages.success(request, f'Profile "{profile.in_game_name}" has been deleted successfully!')
        return redirect('profile_list')
    
    return redirect('display_profile', profile_id=profile_id)
