from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import Profile, Agent, Role, Team, Map, UserProfile
from .forms import ProfileForm, SignUpForm, LoginForm


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _user_owns_profile(user, profile):
    """Return True if the logged-in user owns this profile."""
    return user.is_authenticated and profile.user == user


def _user_has_any_profile(user):
    """Return True if the logged-in user already owns a profile."""
    if not user.is_authenticated:
        return False
    return Profile.objects.filter(user=user).exists()


# ---------------------------------------------------------------------------
# AUTH VIEWS
# ---------------------------------------------------------------------------

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('profile_list')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create the associated UserProfile with Riot credentials
            UserProfile.objects.create(
                user=user,
                riot_id=form.cleaned_data['riot_id'],
                riot_tag=form.cleaned_data.get('riot_tag') or None,
            )
            login(request, user)
            messages.success(request, f'Account created! Welcome, {user.username}.')
            return redirect('profile_list')
    else:
        form = SignUpForm()

    return render(request, 'profiles/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile_list')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'profile_list')
            return redirect(next_url)
    else:
        form = LoginForm(request)

    return render(request, 'profiles/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out.')
    return redirect('profile_list')


# ---------------------------------------------------------------------------
# CLAIM PROFILE VIEW
# ---------------------------------------------------------------------------

@login_required
def claim_profile_view(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)

    # Profile is already claimed
    if profile.is_claimed:
        messages.error(request, 'This profile has already been claimed.')
        return redirect('display_profile', profile_id=profile_id)

    # User already owns a profile
    if _user_has_any_profile(request.user):
        messages.error(request, 'You already have a profile — you cannot claim another.')
        return redirect('display_profile', profile_id=request.user.profile.id)

    # Check riot id/tag match
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'Your account has no Riot ID on file. Please contact support.')
        return redirect('display_profile', profile_id=profile_id)

    user_riot_id = user_profile.riot_id.strip().lower()
    user_riot_tag = (user_profile.riot_tag or '').strip().lower()
    profile_riot_id = profile.riot_id.strip().lower()
    profile_riot_tag = (profile.riot_tag or '').strip().lower()

    if user_riot_id == profile_riot_id and user_riot_tag == profile_riot_tag:
        if request.method == 'POST':
            profile.user = request.user
            profile.save()
            messages.success(request, f'Profile "{profile.in_game_name}" has been claimed!')
            return redirect('display_profile', profile_id=profile_id)
        # GET — show confirmation page
        return render(request, 'profiles/claim_confirm.html', {'profile': profile})
    else:
        messages.error(
            request,
            'Your Riot ID does not match the one saved on this profile. '
            'Only the player whose Riot ID is on the profile can claim it.'
        )
        return redirect('display_profile', profile_id=profile_id)


# ---------------------------------------------------------------------------
# PROFILE VIEWS
# ---------------------------------------------------------------------------

def _lock_riot_fields(form, user):
    """Pre-fill riot_id/riot_tag from the user's UserProfile and mark them readonly."""
    try:
        up = user.userprofile
    except UserProfile.DoesNotExist:
        return
    form.fields['riot_id'].initial = up.riot_id
    form.fields['riot_tag'].initial = up.riot_tag or ''
    for field_name in ('riot_id', 'riot_tag'):
        form.fields[field_name].widget.attrs.update({
            'readonly': True,
            'tabindex': '-1',
            'style': 'opacity: 0.55; cursor: not-allowed; pointer-events: none;',
        })


@login_required(login_url='login_view')
def input_profile(request):
    """Form page to input all profile data."""

    # If logged in and already has a profile, redirect to edit
    if request.user.is_authenticated and _user_has_any_profile(request.user):
        messages.info(
            request,
            'You already have a profile — you can edit yours instead.'
        )
        return redirect('edit_profile', profile_id=request.user.profile.id)

    # Prepare variables for persisting selection on potential error
    selected_agent_ids = []
    selected_role_ids = []
    selected_map_ids = []

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES)

        if request.POST.getlist('agent_id'):
            selected_agent_ids = [int(id) for id in request.POST.getlist('agent_id')]
        if request.POST.getlist('role_id'):
            selected_role_ids = [int(id) for id in request.POST.getlist('role_id')]
        if request.POST.getlist('map_id'):
            selected_map_ids = [int(id) for id in request.POST.getlist('map_id')]

        # Re-apply lock so widget state is correct if form re-renders on error
        if request.user.is_authenticated:
            _lock_riot_fields(profile_form, request.user)

        if profile_form.is_valid():
            profile = profile_form.save(commit=False)

            # Auto-assign to logged-in user and enforce their Riot credentials
            if request.user.is_authenticated:
                profile.user = request.user
                try:
                    up = request.user.userprofile
                    profile.riot_id = up.riot_id
                    profile.riot_tag = up.riot_tag
                except UserProfile.DoesNotExist:
                    pass

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
                    map_ids = map_ids[:3]
                profile.maps.set(map_ids)
            
            messages.success(request, 'Profile created successfully!')
            return redirect('display_profile', profile_id=profile.id)
    else:
        # GET: pre-fill and lock riot fields for logged-in users
        if request.user.is_authenticated:
            try:
                up = request.user.userprofile
                profile_form = ProfileForm(initial={
                    'riot_id': up.riot_id,
                    'riot_tag': up.riot_tag or '',
                })
            except UserProfile.DoesNotExist:
                profile_form = ProfileForm()
            _lock_riot_fields(profile_form, request.user)
        else:
            profile_form = ProfileForm()

    return render(request, 'profiles/input_form.html', {
        'profile_form': profile_form,
        'available_agents': Agent.objects.select_related('role').all(),
        'available_roles': Role.objects.all(),
        'available_teams': Team.objects.all(),
        'available_maps': Map.objects.all(),
        'selected_agent_ids': selected_agent_ids,
        'selected_role_ids': selected_role_ids,
        'selected_map_ids': selected_map_ids,
    })


def display_profile(request, profile_id):
    """Display page showing all profile data."""
    profile = get_object_or_404(Profile, id=profile_id)
    
    teammates = []
    if profile.team:
        teammates = Profile.objects.filter(team=profile.team).exclude(id=profile.id)

    # Does the viewing user already own a different profile?
    user_has_profile = _user_has_any_profile(request.user)

    context = {
        'profile': profile,
        'teammates': teammates,
        'user_has_profile': user_has_profile,
        'is_owner': _user_owns_profile(request.user, profile),
    }
    
    return render(request, 'profiles/display_profile.html', context)


def profile_list(request):
    """List all profiles with optional search/filter."""
    profiles = Profile.objects.all()

    q = request.GET.get('q', '').strip()
    team_filter = request.GET.get('team', '').strip()
    role_filter = request.GET.get('role', '').strip()

    if q:
        profiles = profiles.filter(in_game_name__icontains=q)
    if team_filter == 'free_agent':
        profiles = profiles.filter(team__isnull=True)
    elif team_filter:
        profiles = profiles.filter(team__id=team_filter)
    if role_filter:
        profiles = profiles.filter(roles__id=role_filter)

    # Pass a set of profile IDs owned by this user (for template checks)
    owned_ids = set()
    if request.user.is_authenticated:
        owned_ids = set(Profile.objects.filter(user=request.user).values_list('id', flat=True))
    return render(request, 'profiles/profile_list.html', {
        'profiles': profiles,
        'owned_ids': owned_ids,
        'teams': Team.objects.all().order_by('custom_order', 'name'),
        'roles': Role.objects.all().order_by('name'),
        'q': q,
        'team_filter': team_filter,
        'role_filter': role_filter,
    })


def edit_profile(request, profile_id):
    """Edit an existing profile — owner only."""
    profile = get_object_or_404(Profile, id=profile_id)

    # Only the owner may edit
    if not _user_owns_profile(request.user, profile):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to edit a profile.')
            return redirect('login_view')
        messages.error(request, 'You can only edit your own profile.')
        return redirect('display_profile', profile_id=profile_id)

    selected_agent_ids = []
    selected_role_ids = []
    selected_map_ids = []
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if request.POST.getlist('agent_id'):
            selected_agent_ids = [int(id) for id in request.POST.getlist('agent_id')]
        if request.POST.getlist('role_id'):
            selected_role_ids = [int(id) for id in request.POST.getlist('role_id')]
        if request.POST.getlist('map_id'):
            selected_map_ids = [int(id) for id in request.POST.getlist('map_id')]

        if profile_form.is_valid():
            profile = profile_form.save()
            
            agent_ids = request.POST.getlist('agent_id')
            profile.agents.set(agent_ids if agent_ids else [])
            
            role_ids = request.POST.getlist('role_id')
            profile.roles.set(role_ids if role_ids else [])

            map_ids = request.POST.getlist('map_id')
            if map_ids and len(map_ids) > 3:
                 messages.warning(request, "You can select up to 3 maps. Selection was truncated.")
                 map_ids = map_ids[:3]
            profile.maps.set(map_ids if map_ids else [])
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('display_profile', profile_id=profile.id)
    else:
        profile_form = ProfileForm(instance=profile)
        selected_agent_ids = list(profile.agents.values_list('id', flat=True))
        selected_role_ids = list(profile.roles.values_list('id', flat=True))
        selected_map_ids = list(profile.maps.values_list('id', flat=True))
    
    context = {
        'profile_form': profile_form,
        'profile': profile,
        'is_edit': True,
        'available_agents': Agent.objects.select_related('role').all(),
        'available_roles': Role.objects.all(),
        'available_teams': Team.objects.all(),
        'available_maps': Map.objects.all(),
        'selected_agent_ids': selected_agent_ids,
        'selected_role_ids': selected_role_ids,
        'selected_map_ids': selected_map_ids,
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
        'teammates': teammates
    })


def download_card_png(request, profile_id):
    """Capture the card page at 1920x1080 via Playwright and serve as a PNG download."""
    import traceback as tb_module
    from django.http import HttpResponse, JsonResponse

    get_object_or_404(Profile, id=profile_id)  # 404 guard

    session_cookie = request.COOKIES.get('sessionid')
    csrftoken = request.COOKIES.get('csrftoken')

    # Use localhost internally so Playwright doesn't route through the public internet.
    # Gunicorn must run with --workers > 1 so this internal request gets a free worker
    # (with 1 worker the download view occupies it and Playwright deadlocks waiting for a response).
    # We do NOT set a custom Host header — Chromium rejects Host overrides (ERR_INVALID_ARGUMENT).
    # ALLOWED_HOSTS=['*'] means Django accepts Host: 127.0.0.1:8000 without issue.
    internal_url = f'http://127.0.0.1:8000/profile/{profile_id}/card/?screenshot=1'

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})

            cookies = []
            if session_cookie:
                cookies.append({"name": "sessionid", "value": session_cookie, "domain": "127.0.0.1", "path": "/"})
            if csrftoken:
                cookies.append({"name": "csrftoken", "value": csrftoken, "domain": "127.0.0.1", "path": "/"})
            if cookies:
                context.add_cookies(cookies)

            page = context.new_page()
            page.goto(internal_url, wait_until="networkidle")
            page.wait_for_timeout(2000)  # Let Granim and Anime.js animations settle

            screenshot = page.screenshot(full_page=False)
            browser.close()

        response = HttpResponse(screenshot, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="playercard_{profile_id}.png"'
        return response

    except Exception as exc:
        full_traceback = tb_module.format_exc()
        return JsonResponse(
            {'error': str(exc), 'traceback': full_traceback},
            status=500
        )


def delete_profile(request, profile_id):
    """Delete a profile — owner only."""
    profile = get_object_or_404(Profile, id=profile_id)

    # Only the owner may delete
    if not _user_owns_profile(request.user, profile):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to delete a profile.')
            return redirect('login_view')
        messages.error(request, 'You can only delete your own profile.')
        return redirect('display_profile', profile_id=profile_id)
    
    if request.method == 'POST':
        name = profile.in_game_name
        profile.delete()
        messages.success(request, f'Profile "{name}" has been deleted successfully!')
        return redirect('profile_list')
    
    return redirect('display_profile', profile_id=profile_id)


# ---------------------------------------------------------------------------
# UNCLAIM VIEW
# ---------------------------------------------------------------------------

@login_required
def unclaim_profile_view(request):
    """Remove the ownership link between the logged-in user and their profile."""
    if not _user_has_any_profile(request.user):
        messages.error(request, 'You do not have a claimed profile to unclaim.')
        return redirect('profile_list')

    if request.method == 'POST':
        profile = request.user.profile
        profile_id = profile.id
        profile.user = None
        profile.save()
        messages.success(request, 'Profile unclaimed. You can now claim a different profile.')
        return redirect('display_profile', profile_id=profile_id)

    # GET — show a confirmation page
    profile = request.user.profile
    return render(request, 'profiles/unclaim_confirm.html', {'profile': profile})
