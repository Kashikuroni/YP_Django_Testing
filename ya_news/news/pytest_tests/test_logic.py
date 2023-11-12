from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError

from news.models import Comment
from news.forms import WARNING, BAD_WORDS


@pytest.mark.django_db
def test_auth_user_can_create_comment(
    author_client, detail_url, comments_list, author, create_comment_form
):
    """Может ли авторизированный пользователи создать комментарий в базе."""
    exclude_comments_id = [old_comment.id for old_comment in comments_list]
    author_client.post(detail_url, create_comment_form)
    new_comments = Comment.objects.exclude(id__in=exclude_comments_id)

    assert len(new_comments) == 1
    assert new_comments[0].text == create_comment_form['text']
    assert new_comments[0].author == author


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(
    client, detail_url, comments_list, create_comment_form
):
    """Может ли анонимный пользователь создать комментарий в базе."""
    exclude_comments_id = [old_comment.id for old_comment in comments_list]
    client.post(detail_url, create_comment_form)
    new_comments = Comment.objects.exclude(id__in=exclude_comments_id)

    assert len(new_comments) == 0


@pytest.mark.django_db
def test_bad_words_in_comment(author_client, detail_url):
    """Проверяем комментарии на запрещенные слова."""
    for bad_word in BAD_WORDS:
        form_data = {
            'text': bad_word,
        }
        response = author_client.post(detail_url, form_data)
        assertFormError(
            response, 'form', 'text',
            errors=WARNING
        )


@pytest.mark.django_db
def test_auth_user_can_delete_self_comment(
    author_client, url_to_comments, comment,
    comment_id_for_args, delete_url
):
    """Может ли авторизованный пользователь удалить свой комментарий."""
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)

    comment_is_exists = Comment.objects.filter(
        id=comment_id_for_args[0]
    ).exists()

    assert comment_is_exists is False


@pytest.mark.django_db
def test_auth_user_can_edit_self_comment(
    author_client, comment_id_for_args, url_to_comments,
    comment, edit_url, author, change_comment_form
):
    """Может ли авторизованный пользователь изменить свой комментарий."""
    response = author_client.post(edit_url, data=change_comment_form)
    assertRedirects(response, url_to_comments)

    comment_is_exists = Comment.objects.filter(
        id=comment_id_for_args[0]
    ).exists()
    assert comment_is_exists is True

    comment = Comment.objects.get(id=comment_id_for_args[0])
    assert comment.text == change_comment_form['text']
    assert comment.author == author


@pytest.mark.django_db
def test_auth_user_cant_delete_another_comment(
    comment_id_for_args, comment, reader_client, delete_url
):
    """Может ли авторизованный пользователь удалить чужой комментарий."""
    response = reader_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comment_is_exists = Comment.objects.filter(
        id=comment_id_for_args[0]
    ).exists()

    assert comment_is_exists is True


@pytest.mark.django_db
def test_anonymous_user_cant_edit_another_comment(
    comment_id_for_args, comment,
    reader_client, edit_url, change_comment_form
):
    """Может ли авторизованный пользователь изменить чужой комментарий."""
    response = reader_client.post(edit_url, data=change_comment_form)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comment_is_exists = Comment.objects.filter(
        id=comment_id_for_args[0]
    ).exists()

    assert comment_is_exists is True
    assert comment.text != change_comment_form['text']
