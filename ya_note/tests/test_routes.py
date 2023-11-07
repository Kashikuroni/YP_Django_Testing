# news/tests/test_routes.py
from http import HTTPStatus

# Импортируем функцию для определения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

# Импортируем класс комментария.
from notes.models import Note

# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='1',
            author=cls.author
        )

    def test_pages_availability(self):
        urls = (
            ('notes:home', None, HTTPStatus.OK),
            ('notes:detail', (self.note.slug,), HTTPStatus.FOUND),
            ('users:login', None, HTTPStatus.OK),
            ('users:logout', None, HTTPStatus.OK),
            ('users:signup', None, HTTPStatus.OK),
        )
        for name, args, status in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, status)

    def test_availability_for_auth_client(self):
        names = ('notes:list', 'notes:add', 'notes:list')
        self.client.force_login(self.author)
        for name in names:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_edit_and_delete(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:

            self.client.force_login(user)

            for name in ('notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(
                        'notes:detail', kwargs={'slug': self.note.slug}
                    )
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        names = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:list', None),
            ('notes:edit', (self.note.id,)),
            ('notes:delete', (self.note.id,)),
        )
        login_url = reverse('users:login')

        for name, args in names:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
