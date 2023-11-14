from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты для маршрутизации."""
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

    def setUp(self) -> None:
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.reader_client = Client()
        self.reader_client.force_login(self.reader)

    def test_pages_availability(self):
        """Проверяем доступность страниц."""
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
        """Проверяем доступность страниц авторизованному пользователю."""
        names = ('notes:list', 'notes:add', 'notes:list')
        for name in names:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_edit_and_delete(self):
        """
        Проверяем доступность к страницам редактирования
        для разных пользователей.
        """
        users_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.reader_client, HTTPStatus.NOT_FOUND),
        )
        for custom_client, status in users_statuses:
            for name in ('notes:edit', 'notes:delete'):
                with self.subTest(custom_client=custom_client, name=name):
                    url = reverse(
                        'notes:detail', kwargs={'slug': self.note.slug}
                    )
                    response = custom_client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Проверка переадресации."""
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
