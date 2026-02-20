from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from profiles.models import Role, Agent, Map, Team

class Command(BaseCommand):
    help = 'Sets up the project with initial data: superuser and roles.'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # 1. Handle Superuser
        username = 'admin'
        email = 'admin@example.com'
        password = 'admin'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))
        else:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" password updated.'))

        # 2. Handle Roles
        # Combining standard roles (Duelist, etc) with the custom ones the user had
        roles = [
            {'name': 'Duelist', 'icon_url': 'https://kingdomarchives.com/uploads/agents/roles/Duelist.png'}, 
            {'name': 'Initiator', 'icon_url': 'https://kingdomarchives.com/uploads/agents/roles/Initiator.png'},
            {'name': 'Controller', 'icon_url': 'https://kingdomarchives.com/uploads/agents/roles/Controller.png'}, 
            {'name': 'Sentinel', 'icon_url': 'https://kingdomarchives.com/uploads/agents/roles/Sentinel.png'},
            {'name': '(Extra)IGL', 'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/c/cf/Logo-brain.png'}, 
            {'name': '(Extra)Leader', 'icon_url': 'https://www.pngkey.com/png/full/143-1437226_our-main-qualities-white-leader-icon-png.png'}, 
            {'name': '(Extra)Manager', 'icon_url': 'https://cdn-icons-png.flaticon.com/512/7527/7527248.png'}
        ]
        
        for role_data in roles:
            role, created = Role.objects.update_or_create(
                name=role_data['name'],
                defaults={'icon_url': role_data['icon_url']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Role "{role_data["name"]}" created.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Role "{role_data["name"]}" updated.'))
        
        agents = [
            # duelists
            {'name': 'Waylay', 'role': 'Duelist', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Waylay.png'},
            {'name': 'Jett', 'role': 'Duelist', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Jett.png'},
            {'name': 'Iso', 'role': 'Duelist', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Iso.png'},
            {'name': 'Reyna', 'role': 'Duelist', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Reyna.png'},
            {'name': 'Phoenix', 'role': 'Duelist', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Phoenix.png'},
            {'name': 'Raze', 'role': 'Duelist', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Raze.png'},
            {'name': 'Yoru', 'role': 'Duelist', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Yoru.png'},
            {'name': 'Neon', 'role': 'Duelist', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Neon.png'},
            # initiators
            {'name': 'Sova', 'role': 'Initiator', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Sova.png'},
            {'name': 'Breach', 'role': 'Initiator', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Breach.png'},
            {'name': 'Skye', 'role': 'Initiator', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Skye.png'},
            {'name': 'KAY/O', 'role': 'Initiator', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/KayO.png'},
            {'name': 'Tejo', 'role': 'Initiator', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Tejo.png'},
            {'name': 'Gekko', 'role': 'Initiator', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Gekko.png'},
            {'name': 'Fade', 'role': 'Initiator', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Fade.png'},
            # controllers
            {'name': 'Omen', 'role': 'Controller', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Omen.png'},
            {'name': 'Brimstone', 'role': 'Controller', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Brimstone.png'},
            {'name': 'Viper', 'role': 'Controller', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Viper.png'},
            {'name': 'Clove', 'role': 'Controller', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Clove.png'},
            {'name': 'Astra', 'role': 'Controller', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Astra.png'},
            {'name': 'Harbor', 'role': 'Controller', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Harbor.png'},
            # sentinels
            {'name': 'Sage', 'role': 'Sentinel', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Sage.png'},
            {'name': 'Cypher', 'role': 'Sentinel', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Cypher.png'},
            {'name': 'Killjoy', 'role': 'Sentinel', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Killjoy.png'},
            {'name': 'Deadlock', 'role': 'Sentinel', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Deadlock.png'},
            {'name': 'Veto', 'role': 'Sentinel', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Veto.png'},
            {'name': "Vyse", 'role': 'Sentinel', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Vyse.png'},
            {'name': 'Chamber', 'role': 'Sentinel', 'icon_url': 'https://kingdomarchives.com/uploads/agents/thumbnails/Chamber.png'},
        ]
        
        self.stdout.write("Setting up Agents...")

        for agent_data in agents:
            role_obj = Role.objects.filter(name=agent_data['role']).first()
            if role_obj:
                agent, created = Agent.objects.update_or_create(
                    name=agent_data['name'], 
                    defaults={'role': role_obj, 'icon_url': agent_data['icon_url']}
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
            {'name': 'Ascent', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/e/e7/Loading_Screen_Ascent.png/revision/latest/scale-to-width-down/536?cb=20200607180020'},
            {'name': 'Bind', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/2/23/Loading_Screen_Bind.png/revision/latest/scale-to-width-down/536?cb=20200620202316'},
            {'name': 'Breeze', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/1/10/Loading_Screen_Breeze.png/revision/latest/scale-to-width-down/536?cb=20260106175937'},
            {'name': 'Fracture', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/f/fc/Loading_Screen_Fracture.png/revision/latest/scale-to-width-down/536?cb=20210908143656'},
            {'name': 'Haven', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/7/70/Loading_Screen_Haven.png/revision/latest/scale-to-width-down/536?cb=20200620202335'},
            {'name': 'Icebox', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/1/13/Loading_Screen_Icebox.png/revision/latest?cb=20250730171440'},
            {'name': 'Lotus', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/d/d0/Loading_Screen_Lotus.png/revision/latest?cb=20230106163526'},
            {'name': 'Pearl', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/a/af/Loading_Screen_Pearl.png/revision/latest/scale-to-width-down/536?cb=20220622132842'},
            {'name': 'Split', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/d/d6/Loading_Screen_Split.png/revision/latest/scale-to-width-down/536?cb=20230411161807'},
            {'name': 'Sunset', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/5/5c/Loading_Screen_Sunset.png/revision/latest?cb=20230829125442'},
            {'name': 'Abyss', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/6/61/Loading_Screen_Abyss.png/revision/latest/scale-to-width-down/536?cb=20240730145619'},
            {'name': 'Corrode', 'icon_url': 'https://static.wikia.nocookie.net/valorant/images/6/6f/Loading_Screen_Corrode.png/revision/latest/scale-to-width-down/536?cb=20250624201813'},
        ]
        
        for map_data in maps:
            map_obj, created = Map.objects.update_or_create(
                name=map_data['name'],
                defaults={'icon_url': map_data['icon_url']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Map "{map_data["name"]}" created.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Map "{map_data["name"]}" updated.'))
        
        # 5. Handle Teams
        self.stdout.write("Setting up Teams...")

        teams = [
            {'name': '#1 House of Tyloo', 'icon_url': 'https://imgsvc.trackercdn.com/url/size(128),rgb-map(0.171441,0.003035,0.003035,1;1,0.242281,0.029557,1;0.049707,0.048172,0.051269,1)/https%3A%2F%2Ftrackercdn.com%2Fcdn%2Ftracker.gg%2Fvalorant%2Fpremier%2Fteam-icons%2F2534df0c-4d64-3ef1-2f3b-aabe659233f5.png/image.png'},
            {'name': '#2 Inn of Tyloo', 'icon_url': 'https://imgsvc.trackercdn.com/url/size(128),rgb-map(0.171441,0.003035,0.003035,1;0.323143,0.076185,0.008023,1;0.049707,0.048172,0.051269,1)/https%3A%2F%2Ftrackercdn.com%2Fcdn%2Ftracker.gg%2Fvalorant%2Fpremier%2Fteam-icons%2F2534df0c-4d64-3ef1-2f3b-aabe659233f5.png/image.png'},
            {'name': '#3 Den of Tyloo', 'icon_url': 'https://imgsvc.trackercdn.com/url/size(128),rgb-map(0.887923,0.052861,0.052861,1;1,0.242281,0.029557,1;0.049707,0.048172,0.051269,1)/https%3A%2F%2Ftrackercdn.com%2Fcdn%2Ftracker.gg%2Fvalorant%2Fpremier%2Fteam-icons%2F2534df0c-4d64-3ef1-2f3b-aabe659233f5.png/image.png'},
            {'name': '#4 Nest of Tyloo', 'icon_url': 'https://imgsvc.trackercdn.com/url/size(128),rgb-map(0.171441,0.003035,0.003035,1;1,0.242281,0.029557,1;0.584079,1,0.973446,1)/https%3A%2F%2Ftrackercdn.com%2Fcdn%2Ftracker.gg%2Fvalorant%2Fpremier%2Fteam-icons%2F2534df0c-4d64-3ef1-2f3b-aabe659233f5.png/image.png'},
        ]
        
        for team_data in teams:
            team_obj, created = Team.objects.update_or_create(
                name=team_data['name'],
                defaults={'icon_url': team_data['icon_url']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Team "{team_data["name"]}" created.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Team "{team_data["name"]}" updated.'))

        self.stdout.write(self.style.SUCCESS('Project setup complete.'))