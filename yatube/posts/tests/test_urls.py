from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title='Группа для теста',
            slug='test-slug',
            description='Тестовое описание',
        )
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        url_exists_at_desired = {
            '/posts/index.html': '/',
            '/posts/group_list.html': f'/group/{self.group.slug}/',
            '/posts/profile.html': f'/profile/{self.user.username}/',
            '/posts/post_detail.html': f'/posts/{self.post.id}/',
        }

        for template, address in url_exists_at_desired.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        template_url_names = {
            '/': 'posts/index.html',
            '/create/': 'posts/create_post.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html'
        }
        for address, template in template_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
