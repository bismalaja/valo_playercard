import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from profiles.models import Role, Agent, Map, Team

class Command(BaseCommand):
    help = 'Sets up the project with initial data: superuser and roles.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rotate-admin-password',
            action='store_true',
            help='Rotate bootstrap admin password if the user already exists.',
        )

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # 1. Handle Superuser
        username = os.environ.get('BOOTSTRAP_ADMIN_USERNAME', 'admin')
        email = os.environ.get('BOOTSTRAP_ADMIN_EMAIL', 'admin@example.com')
        password = os.environ.get('BOOTSTRAP_ADMIN_PASSWORD')
        rotate_admin_password = bool(kwargs.get('rotate_admin_password'))
        bootstrap_user = User.objects.filter(username=username).first()

        if not password:
            message = (
                'BOOTSTRAP_ADMIN_PASSWORD is not set. '
                'Skipping bootstrap admin creation/update.'
            )
            if bootstrap_user:
                self.stdout.write(
                    self.style.WARNING(
                        f'{message} Existing superuser "{username}" detected; continuing without admin changes.'
                    )
                )
            elif settings.DEBUG:
                self.stdout.write(self.style.WARNING(message))
            else:
                raise CommandError(
                    'BOOTSTRAP_ADMIN_PASSWORD is required in production when bootstrap admin user '
                    f'"{username}" does not exist.'
                )
        else:
            if bootstrap_user and not rotate_admin_password:
                self.stdout.write(
                    self.style.WARNING(
                        f'Superuser "{username}" already exists. '
                        'Password rotation skipped (use --rotate-admin-password to rotate).'
                    )
                )
            else:
                try:
                    user_for_validation = bootstrap_user or User(username=username, email=email)
                    validate_password(password, user=user_for_validation)
                except ValidationError as exc:
                    raise CommandError(f'Invalid bootstrap admin password: {"; ".join(exc.messages)}') from exc

                if not bootstrap_user:
                    User.objects.create_superuser(username, email, password)
                    self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))
                else:
                    bootstrap_user.email = email
                    bootstrap_user.set_password(password)
                    bootstrap_user.save(update_fields=['email', 'password'])
                    self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" password updated.'))

        # 2. Handle Roles
        # Combining standard roles (Duelist, etc) with the custom ones the user had
        roles = [
            {'name': 'Duelist', 'icon_url': '/static/profiles/images/roles/Duelist.png'}, 
            {'name': 'Initiator', 'icon_url': '/static/profiles/images/roles/Initiator.png'},
            {'name': 'Controller', 'icon_url': '/static/profiles/images/roles/Controller.png'}, 
            {'name': 'Sentinel', 'icon_url': '/static/profiles/images/roles/Sentinel.png'},
            {'name': '(Extra)IGL', 'icon_url': '/static/profiles/images/roles/IGL.png'}, 
            {'name': '(Extra)Leader', 'icon_url': '/static/profiles/images/roles/Leader.png'}, 
            {'name': '(Extra)Manager', 'icon_url': '/static/profiles/images/roles/Manager.png'}
        ]
        
        for role_data in roles:
            role, created = Role.objects.update_or_create(
                name=role_data['name'],
                defaults={'icon_url': role_data['icon_url'], 'icon': None}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Role "{role_data["name"]}" created.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Role "{role_data["name"]}" updated.'))
        
        agents = [
            # duelists
            {'name': 'Waylay', 'role': 'Duelist', 'icon_url': '/static/profiles/images/agents/Waylay.png'},
            {'name': 'Jett', 'role': 'Duelist', 'icon_url': '/static/profiles/images/agents/Jett.png'},
            {'name': 'Iso', 'role': 'Duelist', 'icon_url': '/static/profiles/images/agents/Iso.png'},
            {'name': 'Reyna', 'role': 'Duelist', 'icon_url': '/static/profiles/images/agents/Reyna.png'},
            {'name': 'Phoenix', 'role': 'Duelist', 'icon_url': '/static/profiles/images/agents/Phoenix.png'},
            {'name': 'Raze', 'role': 'Duelist', 'icon_url': '/static/profiles/images/agents/Raze.png'},
            {'name': 'Yoru', 'role': 'Duelist', 'icon_url': '/static/profiles/images/agents/Yoru.png'},
            {'name': 'Neon', 'role': 'Duelist', 'icon_url': '/static/profiles/images/agents/Neon.png'},
            # initiators
            {'name': 'Sova', 'role': 'Initiator', 'icon_url': '/static/profiles/images/agents/Sova.png'},
            {'name': 'Breach', 'role': 'Initiator', 'icon_url': '/static/profiles/images/agents/Breach.png'},
            {'name': 'Skye', 'role': 'Initiator', 'icon_url': '/static/profiles/images/agents/Skye.png'},
            {'name': 'KAY/O', 'role': 'Initiator', 'icon_url': '/static/profiles/images/agents/KayO.png'},
            {'name': 'Tejo', 'role': 'Initiator', 'icon_url': '/static/profiles/images/agents/Tejo.png'},
            {'name': 'Gekko', 'role': 'Initiator', 'icon_url': '/static/profiles/images/agents/Gekko.png'},
            {'name': 'Fade', 'role': 'Initiator', 'icon_url': '/static/profiles/images/agents/Fade.png'},
            # controllers
            {'name': 'Omen', 'role': 'Controller', 'icon_url': '/static/profiles/images/agents/Omen.png'},
            {'name': 'Brimstone', 'role': 'Controller', 'icon_url': '/static/profiles/images/agents/Brimstone.png'},
            {'name': 'Viper', 'role': 'Controller', 'icon_url': '/static/profiles/images/agents/Viper.png'},
            {'name': 'Clove', 'role': 'Controller', 'icon_url': '/static/profiles/images/agents/Clove.png'},
            {'name': 'Astra', 'role': 'Controller', 'icon_url': '/static/profiles/images/agents/Astra.png'},
            {'name': 'Harbor', 'role': 'Controller', 'icon_url': '/static/profiles/images/agents/Harbor.png'},
            # sentinels
            {'name': 'Sage', 'role': 'Sentinel', 'icon_url': '/static/profiles/images/agents/Sage.png'},
            {'name': 'Cypher', 'role': 'Sentinel', 'icon_url': '/static/profiles/images/agents/Cypher.png'},
            {'name': 'Killjoy', 'role': 'Sentinel', 'icon_url': '/static/profiles/images/agents/Killjoy.png'},
            {'name': 'Deadlock', 'role': 'Sentinel', 'icon_url': '/static/profiles/images/agents/Deadlock.png'},
            {'name': 'Veto', 'role': 'Sentinel', 'icon_url': '/static/profiles/images/agents/Veto.png'},
            {'name': "Vyse", 'role': 'Sentinel', 'icon_url': '/static/profiles/images/agents/Vyse.png'},
            {'name': 'Chamber', 'role': 'Sentinel', 'icon_url': '/static/profiles/images/agents/Chamber.png'},
        ]
        
        self.stdout.write("Setting up Agents...")

        for agent_data in agents:
            role_obj = Role.objects.filter(name=agent_data['role']).first()
            if role_obj:
                agent, created = Agent.objects.update_or_create(
                    name=agent_data['name'], 
                    defaults={'role': role_obj, 'icon_url': agent_data['icon_url'], 'icon': None}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Agent "{agent_data["name"]}" created.'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Agent "{agent_data["name"]}" updated.'))
            else:
                self.stdout.write(self.style.WARNING(f'Role "{agent_data["role"]}" not found for agent "{agent_data["name"]}". Skipping.'))

        # 4. Handle Maps
        self.stdout.write("Setting up Maps...")
        
        maps = [
            {'name': 'Ascent',   'icon_url': '/static/profiles/images/maps/Ascent.png'},
            {'name': 'Bind',     'icon_url': '/static/profiles/images/maps/Bind.png'},
            {'name': 'Breeze',   'icon_url': '/static/profiles/images/maps/Breeze.png'},
            {'name': 'Fracture', 'icon_url': '/static/profiles/images/maps/Fracture.png'},
            {'name': 'Haven',    'icon_url': '/static/profiles/images/maps/Haven.png'},
            {'name': 'Icebox',   'icon_url': '/static/profiles/images/maps/Icebox.png'},
            {'name': 'Lotus',    'icon_url': '/static/profiles/images/maps/Lotus.png'},
            {'name': 'Pearl',    'icon_url': '/static/profiles/images/maps/Pearl.png'},
            {'name': 'Split',    'icon_url': '/static/profiles/images/maps/Split.png'},
            {'name': 'Sunset',   'icon_url': '/static/profiles/images/maps/Sunset.png'},
            {'name': 'Abyss',    'icon_url': '/static/profiles/images/maps/Abyss.png'},
            {'name': 'Corrode',  'icon_url': '/static/profiles/images/maps/Corrode.png'},
        ]
        
        for map_data in maps:
            map_obj, created = Map.objects.update_or_create(
                name=map_data['name'],
                defaults={'icon_url': map_data['icon_url'], 'icon': None}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Map "{map_data["name"]}" created.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Map "{map_data["name"]}" updated.'))
        
        # 5. Handle Teams
        self.stdout.write("Setting up Teams...")

        teams = [
            {'name': '#1 House of Tyloo', 'icon_url': '/static/profiles/images/teams/House_of_Tyloo.png'},
            {'name': '#2 Inn of Tyloo',   'icon_url': '/static/profiles/images/teams/Inn_of_Tyloo.png'},
            {'name': '#3 Den of Tyloo',   'icon_url': '/static/profiles/images/teams/Den_of_Tyloo.png'},
            {'name': '#4 Nest of Tyloo',  'icon_url': '/static/profiles/images/teams/Nest_of_Tyloo.png'},
        ]
        
        for team_data in teams:
            team_obj, created = Team.objects.update_or_create(
                name=team_data['name'],
                defaults={'icon_url': team_data['icon_url'], 'icon': None}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Team "{team_data["name"]}" created.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Team "{team_data["name"]}" updated.'))

        self.stdout.write(self.style.SUCCESS('Project setup complete.'))