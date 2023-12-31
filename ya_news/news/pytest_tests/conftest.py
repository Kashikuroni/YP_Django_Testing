# conftest.py
import pytest

from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from django.urls import reverse

from news.models import News, Comment


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create(username='Читатель')


@pytest.fixture
def author_client(author, client):
    client.force_login(author)
    return client


@pytest.fixture
def reader_client(reader, client):
    client.force_login(reader)
    return client


@pytest.fixture
def news():
    news = News.objects.create(
        title='Заголовок',
        text='Текст заметки',
    )
    return news


@pytest.fixture
def comment(news, author):
    comment = Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария'
    )
    return comment


@pytest.fixture
def news_id_for_args(news):
    return news.id,


@pytest.fixture
def comment_id_for_args(comment):
    return comment.id,


@pytest.fixture
def create_news_grt_them_limit() -> None:
    today = datetime.today()
    all_news = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(all_news)


@pytest.fixture
def create_comment_grt_them_limit(news, author) -> None:
    now = timezone.now()
    for index in range(3):
        comment = Comment.objects.create(
            news=news,
            author=author,
            text=f'Текст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()


@pytest.fixture
def home_url() -> str:
    url = reverse('news:home')
    return url


@pytest.fixture
def detail_url(news_id_for_args) -> str:
    url = reverse('news:detail', args=news_id_for_args)
    return url


@pytest.fixture
def edit_url(comment_id_for_args) -> str:
    url = reverse('news:edit', args=comment_id_for_args)
    return url


@pytest.fixture
def delete_url(comment_id_for_args) -> str:
    url = reverse('news:delete', args=comment_id_for_args)
    return url


@pytest.fixture
def url_to_comments(news_id_for_args) -> str:
    news_url = reverse('news:detail', args=news_id_for_args)
    url_to_comments = news_url + '#comments'
    return url_to_comments


@pytest.fixture
def comments_list():
    comment_list = Comment.objects.all()
    return comment_list


@pytest.fixture
def create_comment_form():
    form_data = {
        'text': 'Текст Тестового Комментария.'
    }
    return form_data


@pytest.fixture
def change_comment_form():
    form_data = {
        'text': 'Текс, просто текст. Этого достаточно.'
    }
    return form_data
