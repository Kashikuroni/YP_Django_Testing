from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from news.models import Comment
from news.forms import WARNING, BAD_WORDS


# @pytest.mark.django_db
# @pytest.mark.parametrize(
#     'parametrized_client, expected_comment_count',
#     (
#         (pytest.lazy_fixture('author_client'), 1),
#         (pytest.lazy_fixture('client'), 0),
#     ),
# )
# def test_diff_users_can_create_comment(
#     parametrized_client, expected_comment_count, news_id_for_args, detail_url
# ):
#     """Проверяем могут ли разные пользователи создать комментарий в базе."""
#     TEST_COMMENT_TEXT = 'Текст Тестового Комментария.'
#     old_comment = Comment.objects.all()

#     form_data = {'text': TEST_COMMENT_TEXT, }
#     parametrized_client.post(detail_url, form_data)

#     new_comment = Comment.objects.all()
#     difference = []
#     for new in new_comment:
#         for old in old_comment:
#             if old.id == new.id:
#                 print(old.id, new.id)
#                 difference.append(new)

#     assert len(difference) == expected_comment_count

@pytest.mark.django_db
def test_author_can_create_comment(
    author_client, detail_url, comments_list
):
    """Может ли авторизированный пользователи создать комментарий в базе."""
    test_comment = 'Текст Тестового Комментария.'
    old_comments = comments_list

    exclude_comments_id = []
    for old_comment in old_comments:
        exclude_comments_id.append(old_comment.id)

    form_data = {'text': test_comment, }
    author_client.post(detail_url, form_data)

    new_comments = Comment.objects.exclude(id__in=exclude_comments_id)

    assert len(new_comments) == 1
    assert new_comments[0].text == test_comment


@pytest.mark.django_db
def test_user_cant_create_comment(
    client, detail_url, comments_list
):
    """Может ли не авторизированный пользователь создать комментарий в базе."""
    test_comment = 'Текст Тестового Комментария.'
    old_comments = comments_list

    exclude_comments_id = []
    for old_comment in old_comments:
        exclude_comments_id.append(old_comment.id)

    form_data = {'text': test_comment, }
    client.post(detail_url, form_data)

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
def test_user_can_delete_self_comment(
    author_client, url_to_comments, comment, comment_id_for_args, delete_url
):
    """Может ли не авторизованный пользователь удалить комментарий."""
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)

    new_comment_is_delete = Comment.objects.filter(
        id=comment_id_for_args[0]
    ).exists()

    assert new_comment_is_delete is False


@pytest.mark.django_db
def test_user_can_edit_self_comment(
    author_client, comment_id_for_args, url_to_comments, comment, edit_url
):
    """Может ли не авторизованный пользователь изменить комментарий."""
    edited_text = 'Текс, просто текст. Этого достаточно.'
    form_data = {
        'text': edited_text,
    }
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, url_to_comments)

    new_comment_is_exists = Comment.objects.filter(
        id=comment_id_for_args[0]
    ).exists()
    assert new_comment_is_exists is True

    comment = Comment.objects.get(id=comment_id_for_args[0])
    assert comment.text == edited_text


@pytest.mark.django_db
def test_user_cant_delete_another_comment(
    comment_id_for_args, comment, reader_client, delete_url
):
    """Может ли авторизованный пользователь удалить комментарий."""
    response = reader_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND

    new_comment_is_delete = Comment.objects.filter(
        id=comment_id_for_args[0]
    ).exists()

    assert new_comment_is_delete is True


@pytest.mark.django_db
def test_user_cant_edit_another_comment(
    comment_id_for_args, comment, reader_client
):
    """Может ли авторизованный пользователь изменить комментарий."""
    EDITED_TEXT = 'Текст, просто текст. Этого достаточно.'
    form_data = {
        'text': EDITED_TEXT,
    }
    edit_url = reverse('news:edit', args=comment_id_for_args)
    response = reader_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    found = False
    try:
        comment = Comment.objects.get(id=comment_id_for_args[0])
        assert comment.text != EDITED_TEXT
        found = True
    except ObjectDoesNotExist:
        ...
    assert found is True
