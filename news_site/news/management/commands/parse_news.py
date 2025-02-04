from django.core.management.base import BaseCommand
from news.parsers import parse_news

class Command(BaseCommand):
    help = 'Parse news from a given URL'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='The URL of the RSS feed')

    def handle(self, *args, **kwargs):
        url = kwargs['url']
        parse_news(url)
