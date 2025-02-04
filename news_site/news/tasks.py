from celery import shared_task
from .parsers import parse_news
from django.core.cache import cache

@shared_task
def parse_news_task(url):
    parse_news(url)
    # очистка кэша после парсинга
    cache.delete('news_list')
    