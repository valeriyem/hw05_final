from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test-task',
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )

    def test_models_have_correct_object_names(self):
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_label(self):
        post = PostModelTest.post
        verboses = {
            'text': 'Текст',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, verbose_meaning in verboses.items():
            with self.subTest(verbose_meaning=verbose_meaning):
                verbose = post._meta.get_field(field).verbose_name
                self.assertEqual(verbose, verbose_meaning)
        group = PostModelTest.group
        verbose = group._meta.get_field('title').verbose_name
        self.assertEqual(verbose, 'Заголовок')
        verbose = group._meta.get_field('description').verbose_name
        self.assertEqual(verbose, 'Описание')

    def test_help_text(self):
        post = PostModelTest.post
        help_text = post._meta.get_field('text').help_text
        self.assertEqual(help_text, 'Введите текст поста')
        group = PostModelTest.group
        help_text = group._meta.get_field('title').help_text
        self.assertEqual(help_text, 'Дайте короткое название задаче')
