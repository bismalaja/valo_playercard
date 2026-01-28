from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Profile, Agent, Role, Ability, Team, AbilityTemplate
from .forms import ProfileForm

def input_profile(request):
    """Form page to input all profile data."""
    # Prepare variables for persisting selection on potential error
    selected_agent_ids = []
    selected_role_ids = []

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES)
        
        # If POST, we might need these later if validation fails
        if request.POST.getlist('agent_id'):
            selected_agent_ids = [int(id) for id in request.POST.getlist('agent_id')]
        if request.POST.getlist('role_id'):
            selected_role_ids = [int(id) for id in request.POST.getlist('role_id')]

        if profile_form.is_valid():
            profile = profile_form.save()
            
            # Save selected agents (ManyToMany)
            agent_ids = request.POST.getlist('agent_id')
            print(f"DEBUG: agent_ids = {agent_ids}")
            if agent_ids:
                profile.agents.set(agent_ids)
            
            # Save selected roles (ManyToMany)
            role_ids = request.POST.getlist('role_id')
            print(f"DEBUG: role_ids = {role_ids}")
            if role_ids:
                profile.roles.set(role_ids)
            
            # Save abilities (max 4)
            ability_count = int(request.POST.get('ability_count', 0))
            print(f"DEBUG: ability_count = {ability_count}")
            for i in range(min(ability_count, 4)):
                key_binding = request.POST.get(f'ability_key_{i}')
                ability_name = request.POST.get(f'ability_name_{i}')
                ability_description = request.POST.get(f'ability_description_{i}')
                if key_binding and ability_name and ability_description:
                    # Look up the template for this key
                    template = AbilityTemplate.objects.filter(key_binding=key_binding).first()
                    if template:
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
        'selected_agent_ids': selected_agent_ids,
        'selected_role_ids': selected_role_ids,
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

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        # If POST, we might need these later if validation fails
        if request.POST.getlist('agent_id'):
            selected_agent_ids = [int(id) for id in request.POST.getlist('agent_id')]
        if request.POST.getlist('role_id'):
            selected_role_ids = [int(id) for id in request.POST.getlist('role_id')]

        if profile_form.is_valid():
            profile = profile_form.save()
            
            # Update ManyToMany relationships
            agent_ids = request.POST.getlist('agent_id')
            print(f"DEBUG EDIT: agent_ids = {agent_ids}")
            profile.agents.set(agent_ids if agent_ids else [])
            
            role_ids = request.POST.getlist('role_id')
            print(f"DEBUG EDIT: role_ids = {role_ids}")
            profile.roles.set(role_ids if role_ids else [])
            
            # Delete and recreate abilities
            profile.abilities.all().delete()
            ability_count = int(request.POST.get('ability_count', 0))
            print(f"DEBUG EDIT: ability_count = {ability_count}")
            for i in range(min(ability_count, 4)):
                key_binding = request.POST.get(f'ability_key_{i}')
                ability_name = request.POST.get(f'ability_name_{i}')
                ability_description = request.POST.get(f'ability_description_{i}')
                if key_binding and ability_name and ability_description:
                    # Look up the template for this key
                    template = AbilityTemplate.objects.filter(key_binding=key_binding).first()
                    if template:
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
        'selected_agent_ids': selected_agent_ids,
        'selected_role_ids': selected_role_ids,
    }
    
    return render(request, 'profiles/input_form.html', context)


def delete_profile(request, profile_id):
    """Delete a profile."""
    profile = get_object_or_404(Profile, id=profile_id)
    
    if request.method == 'POST':
        profile.delete()
        messages.success(request, f'Profile "{profile.in_game_name}" has been deleted successfully!')
        return redirect('profile_list')
    
    return redirect('display_profile', profile_id=profile_id)
