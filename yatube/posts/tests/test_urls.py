from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from http import HTTPStatus
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )
        cls.user = User.objects.create_user(username='authorized_client')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.author)
        cache.clear()

    def test_url_exists_at_desired_location(self):
        urls_list = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.author.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/netflix/': HTTPStatus.NOT_FOUND,
            '/create/': HTTPStatus.OK,
        }
        for address, status in urls_list.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_create_post_edit_url_exists_at_desired_location(self):
        """Страницы по адресу /posts/<post_id>/edit/ доступна автору"""
        if self.user == self.post.author:
            response = self.authorized_client.get(f'/posts/{self.post.id}/',
                                                  follow=True)
            self.assertRedirects(response, (f'/posts/{self.post.id}/edit/'))

    def test_urls_uses_correct_template(self):
        """Шаблоны для неавторизированных пользователей"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            # f'/profile/{self.author.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',

        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_for_authorized_uses_correct_templates(self):
        """Шаблоны для авторизированных пользователей"""
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_urls_for_author_uses_correct_templates(self):
        """Шаблоны для автора"""
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_unexisting_page_uses_correct_template(self):
        response = self.authorized_client.get('/unexisting/')
        self.assertTemplateUsed(response, 'core/404.html')
