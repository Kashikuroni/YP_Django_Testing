from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note
from notes.forms import NoteForm


User = get_user_model()


class TestListPage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.another_author = User.objects.create(username='Лев Худой')
        authors_notes = [
            Note(
                title=f'Заметка №{index}',
                text='Просто текст.',
                slug=index,
                author=cls.author,
            )
            for index in range(10)
        ]
        Note.objects.bulk_create(authors_notes)
        another_author_notes = [
            Note(
                title=f'Заметка №{index}',
                text='Просто текст.',
                slug=index,
                author=cls.another_author,
            )
            for index in range(20, 30)
        ]
        Note.objects.bulk_create(another_author_notes)

    def setUp(self) -> None:
        self.authorize_client = Client()
        self.authorize_client.force_login(self.author)

    def test_notes_in_object_list(self):
        """
        Отдельная заметка передаётся на страницу со списком
        заметок в списке `object_list` в словаре `context`.
        """
        url = reverse('notes:list')
        response = self.authorize_client.get(url)
        self.assertIn('object_list', response.context)

    def test_notes_list_not_include_dif_authors(self):
        """
        В список заметок одного пользователя
        не попадают заметки другого пользователя.
        """
        url = reverse('notes:list')
        response = self.authorize_client.get(url)
        notes = response.context['object_list']
        all_authors = [note.author for note in notes]
        diff = [author for author in all_authors if author != self.author]
        self.assertEqual(diff, [])


class TestDetailPage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.note = Note.objects.create(
            title=f'Заметка №{1}',
            text='Просто текст.',
            slug=1,
            author=cls.author,
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))

    def setUp(self) -> None:
        self.authorize_client = Client()
        self.authorize_client.force_login(self.author)

    def test_anonymous_client_has_no_form(self):
        """Анонимный пользователь не получает форму."""
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_authorized_client_has_form(self):
        """На страницы создания и редактирования заметки передаются формы."""
        response = self.authorize_client.get(self.edit_url)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertTrue(isinstance(form, NoteForm))
