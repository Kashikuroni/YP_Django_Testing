from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify
from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class TestNoteAddEditDelete(TestCase):
    NOTE_TEXT = 'Текст комментария'
    NEW_NOTE_TEXT = 'Обновлённый комментарий'

    @classmethod
    def setUpTestData(cls):
        cls.author_client = Client()
        cls.author = User.objects.create(username='Лев Толстой')
        cls.note = Note.objects.create(
            title=f'Заметка №{1}',
            text=cls.NOTE_TEXT,
            slug=1,
            author=cls.author,
        )
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.success_url = reverse('notes:success')
        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {
            'text': cls.NEW_NOTE_TEXT,
        }

    def test_author_can_add(self):
        """Залогиненный пользователь может создать заметку."""
        response = self.author_client.get(self.add_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_anonym_cant_add(self):
        """Анонимный не может создать заметку."""
        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_is_not_possible_create_two_notes_same_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        form_data = {
            'title': 'Тестовая заметка',
            'text': 'Тестовый текст',
            'slug': 1,
        }
        response = self.author_client.post(self.add_url, data=form_data)
        self.assertFormError(
            response, 'form', 'slug',
            errors=('1' + WARNING)
        )

    def test_author_can_delete_comment(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_comment_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_comment(self):
        form_data = {
            'title': 'Тестовая заметка',
            'text': self.NEW_NOTE_TEXT,
            'slug': 1,
        }
        response = self.author_client.post(
            self.edit_url, data=form_data
        )
        self.assertRedirects(response, self.success_url,)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_comment_of_another_user(self):
        response = self.reader_client.post(
            self.edit_url, data=self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)


class TestNoteSlug(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author_client = Client()
        cls.author = User.objects.create(username='Лев Толстой')
        cls.author_client.force_login(cls.author)

    def test_empty_slug(self):
        url = reverse('notes:add')
        form_data = {
            'title': 'Тестовая заметка',
            'text': 'Тестовый текст',
        }
        response = self.author_client.post(url, data=form_data)

        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)

        new_note = Note.objects.get()
        expected_slug = slugify(form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)
