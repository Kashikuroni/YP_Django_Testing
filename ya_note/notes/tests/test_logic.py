from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()


class TestNoteAddEditDelete(TestCase):
    """Тесты взаимодействия с заметками."""
    NOTE_TEXT = 'Текст комментария'
    NEW_NOTE_TEXT = 'Обновлённый комментарий'
    TEST_SLUG = 3

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заметка №1',
            text=cls.NOTE_TEXT,
            slug='1',
            author=cls.author,
        )

        cls.success_url = reverse('notes:success')
        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.edit_note_form_data = {
            'text': cls.NEW_NOTE_TEXT,
        }
        cls.create_note_form_data = {
            'title': f'Заметка №{3}',
            'text': cls.NOTE_TEXT,
            'slug': cls.TEST_SLUG,
        }

    def setUp(self) -> None:
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.reader_client = Client()
        self.reader_client.force_login(self.reader)

    def test_author_can_add(self):
        """Залогиненный пользователь может создать заметку."""
        response = self.author_client.post(
            self.add_url, data=self.create_note_form_data
        )
        self.assertRedirects(response, self.success_url)
        comment_is_exists = Note.objects.filter(
            slug=self.TEST_SLUG
        ).exists()
        self.assertTrue(comment_is_exists)

        note = Note.objects.get(slug=self.TEST_SLUG)
        self.assertEqual(note.title, self.create_note_form_data['title'])
        self.assertEqual(note.text, self.create_note_form_data['text'])
        self.assertEqual(note.author, self.author)

    def test_anonym_cant_add(self):
        """Анонимный не может создать заметку."""
        self.client.post(self.add_url, data=self.create_note_form_data)
        comment_is_exists = Note.objects.filter(
            slug=self.TEST_SLUG
        ).exists()

        self.assertFalse(comment_is_exists)

    def test_is_not_possible_create_two_notes_same_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        exists_note_form_data = {
            'title': 'Тестовая заметка',
            'text': 'Тестовый текст',
            'slug': 1,
        }
        response = self.author_client.post(
            self.add_url, data=exists_note_form_data
        )
        self.assertFormError(
            response, 'form', 'slug',
            errors=('1' + WARNING)
        )

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        old_note_count = len(Note.objects.all())
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)

        notes_exists = Note.objects.filter(slug=self.note.slug).exists()
        self.assertFalse(notes_exists)

        new_note_count = len(Note.objects.all())
        self.assertEqual((old_note_count - new_note_count), 1)

    def test_user_cant_delete_note_of_another_user(self):
        """Пользователь не может удалить заметку чужую заметку."""
        old_note_count = len(Note.objects.all())
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        notes_exists = Note.objects.filter(slug=self.note.slug).exists()
        self.assertTrue(notes_exists)

        new_note_count = len(Note.objects.all())
        self.assertEqual((old_note_count - new_note_count), 0)

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        form_data = {
            'title': 'Тестовая заметка',
            'text': self.NEW_NOTE_TEXT,
            'slug': '1',
        }
        response = self.author_client.post(
            self.edit_url, data=form_data
        )
        self.assertRedirects(response, self.success_url,)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, form_data['title'])
        self.assertEqual(self.note.text, form_data['text'])
        self.assertEqual(self.note.slug, form_data['slug'])
        self.assertEqual(self.note.author, self.author)

    def test_user_cant_edit_note_of_another_user(self):
        """Пользователь не может редактировать чужую заметку."""
        response = self.reader_client.post(
            self.edit_url, data=self.edit_note_form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        form_data = {
            "title": 'Заметка №1',
            "text": self.NOTE_TEXT,
            "slug": '1',
            "author": self.author,
        }
        self.assertEqual(self.note.text, form_data['text'])
        self.assertEqual(self.note.title, form_data['title'])
        self.assertEqual(self.note.slug, form_data['slug'])
        self.assertEqual(self.note.author, form_data['author'])


class TestNoteSlug(TestCase):
    """Тесты для поля slug."""
    @classmethod
    def setUpTestData(cls):
        cls.author_client = Client()
        cls.author = User.objects.create(username='Лев Толстой')
        cls.author_client.force_login(cls.author)

    def test_empty_slug(self):
        """Проверка генерации поля slug."""
        url = reverse('notes:add')
        form_data = {
            'title': 'Тестовая заметка',
            'text': 'Тестовый текст',
        }
        response = self.author_client.post(url, data=form_data)

        self.assertRedirects(response, reverse('notes:success'))

        new_note = Note.objects.get()
        expected_slug = slugify(form_data['title'])
        note_empty_slug_is_exists = Note.objects.filter(
            slug=expected_slug
        ).exists()

        self.assertTrue(note_empty_slug_is_exists)
        self.assertEqual(new_note.slug, expected_slug)
