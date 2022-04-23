import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestMan')
        cls.user2 = User.objects.create_user(username='User2')
        cls.user3 = User.objects.create_user(username='User3')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug_1',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Тестовый Текстовый пост ',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostViewTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user2 = PostViewTest.user2
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        self.user3 = PostViewTest.user3

    def test_pages_uses_correct_template(self):
        """Проверяем правильные ли html-шаблоны используются."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Главная.Проверяем соответствует ли ожиданиям словарь context."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_title = first_object.group.title
        post_post = first_object.text
        post_image = first_object.image.name
        self.assertEqual(post_title, self.group.title)
        self.assertEqual(post_post, self.post.text)
        self.assertEqual(post_image, self.post.image.name)

    def test_group_posts_page_show_correct_context(self):
        """Группа.Проверяем соответствует ли ожиданиям словарь context."""
        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        post_group_description_0 = first_object.group.description
        post_image = first_object.image.name
        self.assertEqual(post_image, self.post.image.name)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group.title)
        self.assertEqual(post_group_description_0, self.group.description)

    def test_profile_page_show_correct_context(self):
        """Профиль.Проверяем соответствует ли ожиданиям словарь context."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'TestMan'})
        )
        first_object = response.context['page_obj'][0]
        profile_title = first_object.group.title
        profile_slug = first_object.group.slug
        profile_text = first_object.text
        post_image = first_object.image.name
        self.assertEqual(post_image, self.post.image.name)
        self.assertEqual(profile_title, self.group.title)
        self.assertEqual(profile_text, self.post.text)
        self.assertEqual(profile_slug, self.group.slug)

    def test_post_detail_page_show_correct_context(self):
        """Отдельный пост.Проверяем словарь context."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            response.context.get('post').group.title, self.group.title
        )
        self.assertEqual(
            response.context.get('post').group.slug, self.group.slug
        )
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(
            response.context.get('post').image.name, self.post.image.name
        )

    def test_create_post_page_show_correct_context(self):
        """Форма создания поста.Проверяем словарь context."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_show_correct_context(self):
        """Форма редактирования поста.Проверяем словарь context."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context.get('is_edit'))

    def test_authorized_client_can_add_comments(self):
        ''' Авторизированный клиент может оставлять комментарии '''
        count_comments = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
            'post': self.post
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=False
        )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(Comment.objects.count(), count_comments + 1)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )

    def test_guest_can_not_comment(self):
        ''' Неавторизованный клиент не может оставить комментарий '''
        count_comments = Comment.objects.count()
        form_data = {
            'text': 'Коммент',
            'post': self.post
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(count_comments, Comment.objects.count())

    def test_index_cache(self):
        cache.clear()
        response_one = self.guest_client.get(reverse('posts:index'))
        response_one_content = response_one.content
        response_one.context['page_obj'][0].delete()
        form_data = {
            'text': 'Тестовый текст',
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response_two = self.guest_client.get(reverse('posts:index'))
        response_two_content = response_two.content
        self.assertEqual(response_one_content, response_two_content)
        cache.clear()
        response_three = self.guest_client.get(reverse('posts:index'))
        response_three_content = response_three.content
        self.assertNotEqual(response_two_content, response_three_content)

    def test_follow(self):
        ''' Авторизованнный клиент может подписаться на автора '''
        self.assertFalse(Follow.objects.filter(
            user=self.user2,
            author=self.user
        ).exists())
        self.authorized_client2.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user})
        )
        self.assertTrue(Follow.objects.filter(
            user=self.user2,
            author=self.user,
        ).exists())

    def test_unfollow(self):
        ''' Авторизованнный клиент может отподписаться на автора '''
        Follow.objects.create(user=self.user2, author=self.user)
        self.assertTrue(Follow.objects.filter(
            user=self.user2,
            author=self.user
        ).exists())
        self.authorized_client2.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user})
        )
        self.assertFalse(Follow.objects.filter(
            user=self.user2,
            author=self.user
        ).exists())

    def test_new_post_in_follower_index(self):
        Follow.objects.create(user=self.user2, author=self.user)
        Post.objects.create(
            text='Тестовый текст',
            author=self.user
        )
        response = self.authorized_client2.get(reverse('posts:follow_index'))
        post = response.context.get('page_obj')[0]
        response2 = self.authorized_client.get(reverse('posts:follow_index'))
        post2 = response2.context.get('page_obj')
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertFalse(post2)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class PostPaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestMan')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(settings.OBJ_IN_PAGE * 2):
            cls.post = Post.objects.create(
                group=cls.group,
                author=cls.user,
                text='Тестовый Текстовый пост ',
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.cnt_obj = Post.objects.count()

    def test_first_page_records_index(self):
        """Главная.Проверяем пагинатор на первой странице."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']), settings.OBJ_IN_PAGE
        )

    def test_second_page_records_index(self):
        """Главная.Проверяем пагинатор на второй странице."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(
            response.context['page_obj']), self.cnt_obj - settings.OBJ_IN_PAGE
        )

    def test_first_page_records_group_list(self):
        """Группа.Проверяем пагинатор на первой странице группы."""
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(
            len(response.context['page_obj']), settings.OBJ_IN_PAGE
        )

    def test_second_page_records_group_list(self):
        """Группа.Проверяем пагинатор на второй странице группы."""
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}) + '?page=2'
        )
        self.assertEqual(len(
            response.context['page_obj']), self.cnt_obj - settings.OBJ_IN_PAGE
        )

    def test_first_page_records_profile(self):
        """Профиль.Проверяем пагинатор на первой странице."""
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': 'TestMan'})
        )
        self.assertEqual(
            len(response.context['page_obj']), settings.OBJ_IN_PAGE
        )

    def test_second_page_records_profile(self):
        """Профиль.Проверяем пагинатор на второй странице."""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'TestMan'}) + '?page=2'
        )
        self.assertEqual(len(
            response.context['page_obj']), self.cnt_obj - settings.OBJ_IN_PAGE
        )
