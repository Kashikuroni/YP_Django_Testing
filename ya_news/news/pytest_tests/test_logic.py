import pytest
from http import HTTPStatus
from pytest_django.asserts import assertRedirects, assertFormError

from django.urls import reverse

from news.models import Comment
from news.forms import WARNING, BAD_WORDS


@pytest.mark.django_db
@pytest.mark.parametrize(
    'parametrized_client, expected_comment_count',
    (
        (pytest.lazy_fixture('author_client'), 1),
        (pytest.lazy_fixture('client'), 0),
    ),
)
def test_anonymous_user_cant_create_comment(
    parametrized_client, news_id_for_args, expected_comment_count
):
    url = reverse('news:detail', args=news_id_for_args)
    form_data = {
        'text': 'Текст Комментария.'
    }
    parametrized_client.post(url, form_data)
    comments_count = Comment.objects.count()
    assert comments_count == expected_comment_count


@pytest.mark.django_db
def test_bad_words_in_comment(author_client, news_id_for_args):
    url = reverse('news:detail', args=news_id_for_args)
    for bad_word in BAD_WORDS:
        form_data = {
            'text': bad_word,
        }
        response = author_client.post(url, form_data)
        assertFormError(
            response, 'form', 'text',
            errors=WARNING
        )


@pytest.mark.django_db
def test_user_can_delete_self_comment(
    author_client, news_id_for_args, url_to_comments, comment
):
    delete_url = reverse('news:delete', args=news_id_for_args)
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)
    comment_count = Comment.objects.count()
    assert comment_count == 0


@pytest.mark.django_db
def test_user_can_edit_self_comment(
    author_client, news_id_for_args, url_to_comments, comment
):
    form_data = {
        'text': 'Текс, просто текст. Этого достаточно.',
    }
    edit_url = reverse('news:edit', args=news_id_for_args)
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, url_to_comments)
    comment_count = Comment.objects.count()
    assert comment_count == 1


@pytest.mark.django_db
def test_user_cant_delete_another_comment(
    news_id_for_args, url_to_comments, comment, reader_client
):
    delete_url = reverse('news:delete', args=news_id_for_args)
    response = reader_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_count = Comment.objects.count()
    assert comment_count == 1


@pytest.mark.django_db
def test_user_cant_edit_another_comment(
    news_id_for_args, url_to_comments, comment, reader_client
):
    form_data = {
        'text': 'Текс, просто текст. Этого достаточно.',
    }
    edit_url = reverse('news:edit', args=news_id_for_args)
    response = reader_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_count = Comment.objects.count()
    assert comment_count == 1
