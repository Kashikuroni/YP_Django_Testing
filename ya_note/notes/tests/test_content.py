from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.models import Note


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

    def test_notes_in_object_list(self):
        """
        Отдельная заметка передаётся на страницу со списком
        заметок в списке `object_list` в словаре `context`.
        """
        url = reverse('notes:list')
        self.client.force_login(self.author)
        response = self.client.get(url)
        self.assertIn('object_list', response.context)

    def test_notes_list_not_include_dif_authors(self):
        """
        В список заметок одного пользователя
        не попадают заметки другого пользователя.
        """
        url = reverse('notes:list')
        self.client.force_login(self.author)
        response = self.client.get(url)
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

    def test_anonymous_client_has_no_form(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_authorized_client_has_form(self):
        """На страницы создания и редактирования заметки передаются формы."""
        self.client.force_login(self.author)
        response = self.client.get(self.edit_url)
        self.assertIn('form', response.context)
