import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.form = PostForm()
        cls.user = User.objects.create_user(username='test_user')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_user = Client()
        self.author_client = Client()
        self.author_client.force_login(PostFormTests.author)

    def test_create_post(self):
        """Валидная форма создает запись"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'image': self.uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               args=(self.author.username,)))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit(self):
        post_id = Post.objects.get(id=self.post.id)
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст'
        }
        response = self.author_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(self.post.id,)))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(Post.objects.get(id=self.post.id), post_id)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый текст',
            author=cls.author,
        )
        cls.user = User.objects.create_user(username='test_user')

    def setUp(self):
        self.guest_user = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_create_comment_for_authorized_user(self):
        comment_count = Comment.objects.count()
        print(Comment.objects.count())
        form_data = {
            'text': 'Текст комментария',
        }
        self.author_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_for_nonauthorized_user(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария', }
        self.guest_user.get(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
