import pytest

from django.conf import settings

from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count(client, create_news_grt_them_limit, home_url):
    """Тестируем кол-во новостей в пагинаторе."""
    response = client.get(home_url)
    object_list = response.context['object_list']
    news_count = len(object_list)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, create_news_grt_them_limit, home_url):
    """Тестируем сортировку новостей по дате публикации."""
    response = client.get(home_url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert sorted_dates == all_dates


@pytest.mark.django_db
def test_comments_order(
    client, detail_url, create_comment_grt_them_limit
):
    """Тестируем сортировку комментариев по дате добавления."""
    response = client.get(detail_url)
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    comments_dates = [comment.created for comment in all_comments]
    sorted_comments_dates = sorted(comments_dates, reverse=False)
    assert sorted_comments_dates == comments_dates


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, detail_url):
    """Тестируем доступ анонимного пользователя к форме комментария."""
    response = client.get(detail_url)
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_form(author_client, detail_url):
    """Тестируем доступ авторизованного пользователя к форме комментария."""
    response = author_client.get(detail_url)
    form = response.context['form']
    assert form.__class__ == CommentForm
