from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache

import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.models import Group, Post, Follow

User = get_user_model()

POSTS_PER_PAGE = 10
NEXT_PAGE_POSTS = 5


class PostPagesTests(TestCase):
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
        self.author_client.force_login(PostPagesTests.author)
        # cache.clear()

    def test_cache_index_page_correct(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.content
        response_old_post = self.authorized_client.get(reverse('posts:index'))
        old_post = response_old_post.content
        self.assertEqual(old_post, post)
        cache.clear()
        response_new_post = self.authorized_client.get(reverse('posts:index'))
        new_post = response_new_post.content
        self.assertNotEqual(old_post, new_post)

    def test_pages_uses_correct_template(self):
        cache.clear()
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_list',
                                             args=(self.group.slug,)),
            'posts/profile.html': reverse('posts:profile',
                                          args=(self.author.username,)),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              args=(self.post.id,)),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        object = response.context.get('page_obj')
        self.assertEqual(object.object_list, list(Post.objects.all()))

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list', args=(self.group.slug,))
        )
        object = response.context.get('page_obj')
        group_object = response.context.get('group')
        self.assertEqual(object.object_list, list(Post.objects.all()))
        self.assertEqual(group_object, Group.objects.get())

    def test_profile_page_show_correct_context(self):
        response = self.author_client.get(reverse(
            'posts:profile',
            args=(self.author.username,))
        )
        object = response.context.get('page_obj')
        username_object = response.context.get('username')
        author_object = response.context.get('author')
        posts_count_object = response.context.get('posts_count')
        self.assertEqual(list(object), list(Post.objects.all()))
        self.assertEqual(username_object, User.objects.all()[0].username)
        self.assertEqual(author_object, User.objects.all()[0])
        self.assertEqual(posts_count_object, Post.objects.all().count())

    def test_post_detail_page_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:post_detail',
                                                 args=(self.post.id,)))
        propose_post_object = response.context.get('post')
        propose_author_object = response.context.get('author')
        post_counts_object = response.context.get('posts_count')
        self.assertEqual(propose_post_object, Post.objects.get())
        self.assertEqual(propose_author_object, User.objects.all()[0])
        self.assertEqual(post_counts_object, Post.objects.all().count())

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        response = self.author_client.get(reverse(
            'posts:post_edit',
            args=(self.post.id,))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='description',
        )
        for _ in range(POSTS_PER_PAGE + NEXT_PAGE_POSTS):
            Post.objects.create(
                text='text',
                author=cls.author,
                group=cls.group,
            )

    def setUp(self):
        self.client = Client()
        self.author_client = Client()
        self.author_client.force_login(PaginatorViewsTest.author)

    def test_index(self):
        for page in (1, 2):
            response = self.client.get(
                reverse(
                    'posts:index',
                ),
                [
                    ('page', page),
                ]
            )
            object = response.context['page_obj']
            if page == 1:
                self.assertEqual(len(object.object_list), POSTS_PER_PAGE)
            elif page == 2:
                self.assertEqual(len(object.object_list), NEXT_PAGE_POSTS)

    def test_group_list(self):
        for page in (1, 2):
            response = self.client.get(
                reverse(
                    'posts:group_list', args=(self.group.slug,),
                ),
                [
                    ('page', page),
                ]
            )
            object = response.context['page_obj']
            if page == 1:
                self.assertEqual(len(object.object_list), POSTS_PER_PAGE)
            elif page == 2:
                self.assertEqual(len(object.object_list), NEXT_PAGE_POSTS)

    def test_profile(self):
        for page in (1, 2):
            response = self.author_client.get(
                reverse(
                    'posts:profile', args=(self.author.username,),
                ),
                [
                    ('page', page),
                ]
            )
            object = response.context['page_obj']
            if page == 1:
                self.assertEqual(len(object.object_list), POSTS_PER_PAGE)
            elif page == 2:
                self.assertEqual(len(object.object_list), NEXT_PAGE_POSTS)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    def setUp(self):
        super().setUp()
        self.guest_user = Client()
        self.user = User.objects.create_user(username='test_user')
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        self.group1 = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group1,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_index_page_show_correct_context(self):
        cache.clear()
        propose_post = self.guest_user.get(
            reverse('posts:index')).context['page_obj'][0]
        self.assertEqual(propose_post.image, self.post.image)

    def test_group_page_show_correct_context(self):
        propose_post = self.authorized_user.get(
            reverse('posts:group_list',
                    args=(self.group1.slug,))).context['page_obj'][0]
        self.assertEqual(propose_post.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        propose_post = self.authorized_user.get(
            reverse('posts:profile',
                    args=(self.user.username,))).context['page_obj'][0]
        self.assertEqual(propose_post.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        propose_post = self.authorized_user.get(reverse(
            'posts:post_detail', args=(self.post.id,))).context['post']
        self.assertEqual(propose_post.image, self.post.image)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.author = User.objects.create_user(username='auth')
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author,
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(FollowViewsTest.author)

    def test_follow(self):
        author_count = Follow.objects.count()
        print('VEVLELV')
        print(author_count)
        self.authorized_client.get(
            reverse('posts:profile_follow', args=(self.author.username,)),
        )
        self.assertEqual(Follow.objects.count(), author_count)

    def test_unfollow(self):
        author_count = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=(self.author.username,)),
        )
        self.assertEqual(Follow.objects.count(), author_count - 1)

    def test_follow_page(self):
        self.authorized_client.get(reverse(
            'posts:profile_follow', args=(self.author.username,)))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertContains(response, self.post.text)

    def test_unfollow_page(self):
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', args=(self.author.username,)))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, self.post.text)
