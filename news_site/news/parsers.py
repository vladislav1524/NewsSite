import requests
from bs4 import BeautifulSoup
from .models import News

def parse_news(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml-xml')

    items = soup.find_all('item')[:10] # последние 10 новостей

    for item in items:
        title = item.find('title').text if item.find('title') else 'Нет загаловка'
        link = item.find('link').text if item.find('link') else '/no-link'
        description = item.find('description').text if item.find('description') else 'Нет описания'
        pub_date = item.find('pubDate').text if item.find('pubDate') else None

        if not News.objects.filter(url=link).exists():
            News.objects.create(
                title=title,
                content=description,
                url=link,
                published_date = pub_date
            )
