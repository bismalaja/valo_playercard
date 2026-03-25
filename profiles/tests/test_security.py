import io
import json
from unittest.mock import patch

from PIL import Image
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from profiles.forms import ProfileForm
from profiles.models import Profile, UserProfile


# class SecurityViewTests(TestCase):
#     def setUp(self):
#         cache.clear()

#     def test_login_rejects_external_next_redirect(self):
#         user = User.objects.create_user(username='safeuser', password='StrongPass123!')

#         response = self.client.post(
#             reverse('login_view') + '?next=https://evil.example/phish',
#             {'username': user.username, 'password': 'StrongPass123!'},
#         )

#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(response.url, reverse('profile_list'))

#     def test_logout_requires_post_and_csrf(self):
#         user = User.objects.create_user(username='logoutuser', password='StrongPass123!')

#         # Method enforcement
#         self.client.force_login(user)
#         get_response = self.client.get(reverse('logout_view'))
#         self.assertEqual(get_response.status_code, 405)

#         # CSRF enforcement for state-changing POST
#         csrf_client = Client(enforce_csrf_checks=True)
#         csrf_client.force_login(user)
#         post_response = csrf_client.post(reverse('logout_view'))
#         self.assertEqual(post_response.status_code, 403)

#     def test_delete_requires_post(self):
#         owner = User.objects.create_user(username='owner', password='StrongPass123!')
#         profile = Profile.objects.create(
#             in_game_name='OwnerProfile',
#             riot_id='Owner',
#             riot_tag='#NA1',
#             user=owner,
#         )

#         self.client.force_login(owner)
#         response = self.client.get(reverse('delete_profile', args=[profile.id]))
#         self.assertEqual(response.status_code, 405)

#     def test_claim_second_user_is_blocked_after_first_claim(self):
#         user_one = User.objects.create_user(username='user_one', password='StrongPass123!')
#         user_two = User.objects.create_user(username='user_two', password='StrongPass123!')

#         UserProfile.objects.create(user=user_one, riot_id='Tyloo', riot_tag='#NA1')
#         UserProfile.objects.create(user=user_two, riot_id='Tyloo', riot_tag='#NA1')

#         profile = Profile.objects.create(
#             in_game_name='Unclaimed',
#             riot_id='Tyloo',
#             riot_tag='#NA1',
#             user=None,
#         )

#         self.client.force_login(user_one)
#         first_response = self.client.post(reverse('claim_profile', args=[profile.id]))
#         self.assertEqual(first_response.status_code, 302)

#         self.client.logout()
#         self.client.force_login(user_two)
#         second_response = self.client.post(reverse('claim_profile', args=[profile.id]))
#         self.assertEqual(second_response.status_code, 302)

#         profile.refresh_from_db()
#         self.assertEqual(profile.user_id, user_one.id)

#     @patch('profiles.views_tracker.fetch_tracker_profile')
#     def test_tracker_endpoint_rate_limit_returns_429(self, mock_fetch):
#         mock_fetch.return_value = {'peak_rank': 'Gold', 'peak_rank_icon': 'https://example.com/rank.png'}

#         user = User.objects.create_user(username='tracker_user', password='StrongPass123!')
#         self.client.force_login(user)

#         url = reverse('fetch_tracker_stats')
#         payload = json.dumps({'riot_id': 'Tyloo', 'riot_tag': '#NA1'})

#         last_response = None
#         for _ in range(11):
#             last_response = self.client.post(url, data=payload, content_type='application/json')

#         self.assertIsNotNone(last_response)
#         self.assertEqual(last_response.status_code, 429)
#         body = last_response.json()
#         self.assertIn('Please wait', body.get('error', ''))


# class UploadValidationTests(TestCase):
#     def _valid_png_bytes(self):
#         buffer = io.BytesIO()
#         image = Image.new('RGB', (8, 8), color='red')
#         image.save(buffer, format='PNG')
#         return buffer.getvalue()

#     def test_profile_form_rejects_disallowed_extension(self):
#         file_obj = SimpleUploadedFile(
#             'avatar.exe',
#             self._valid_png_bytes(),
#             content_type='image/png',
#         )

#         form = ProfileForm(
#             data={
#                 'in_game_name': 'PlayerOne',
#                 'riot_id': 'Tyloo',
#                 'riot_tag': '#NA1',
#                 'profile_picture_url': '',
#                 'bio': '',
#             },
#             files={'profile_picture': file_obj},
#         )

#         self.assertFalse(form.is_valid())
#         self.assertIn('Only .jpg, .jpeg, .png, and .webp files are allowed.', form.errors['profile_picture'])

#     def test_profile_form_rejects_oversized_upload(self):
#         oversized = SimpleUploadedFile(
#             'avatar.png',
#             b'\x89PNG\r\n\x1a\n' + (b'a' * ((5 * 1024 * 1024) + 10)),
#             content_type='image/png',
#         )

#         form = ProfileForm(
#             data={
#                 'in_game_name': 'PlayerTwo',
#                 'riot_id': 'Tyloo2',
#                 'riot_tag': '#NA2',
#                 'profile_picture_url': '',
#                 'bio': '',
#             },
#             files={'profile_picture': oversized},
#         )

#         self.assertFalse(form.is_valid())
#         self.assertIn('Image must be 5MB or smaller.', form.errors['profile_picture'])

#     def test_profile_form_accepts_valid_upload(self):
#         valid = SimpleUploadedFile(
#             'avatar.png',
#             self._valid_png_bytes(),
#             content_type='image/png',
#         )

#         form = ProfileForm(
#             data={
#                 'in_game_name': 'PlayerThree',
#                 'riot_id': 'Tyloo3',
#                 'riot_tag': '#NA3',
#                 'profile_picture_url': '',
#                 'bio': 'hello',
#             },
#             files={'profile_picture': valid},
#         )

#         self.assertTrue(form.is_valid(), msg=form.errors.as_json())
