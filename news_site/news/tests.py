from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, Mock
from .models import News, ReadLater
from .forms import CustomSignupForm, EmailForm
from .parsers import parse_news
from .tasks import parse_news_task

# тесты представлений
class NewsTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser',
                                                    password='testpassword',
                                                    email='test@example.com')
        self.news = News.objects.create(
            title='Test News',
            content='This is a test news content.',
            url='https://example.com',
            published_date='Wed, 22 Jan 2025 15:23:09 +0300'
        )

    def test_news_list_view(self):
        self.client.login(username='test@example.com', password='testpassword')
        self.assertTrue(self.client.login(username='test@example.com', password='testpassword'))
        response = self.client.get(reverse('news:news_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test News')

    def test_add_to_read_later(self):
        self.client.login(username='test@example.com', password='testpassword')
        self.assertTrue(self.client.login(username='test@example.com', password='testpassword'))
        response = self.client.post(reverse('news:add_to_read_later', args=[self.news.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ReadLater.objects.filter(user=self.user, news=self.news).exists())

    def test_remove_from_read_later(self):
        self.client.login(username='test@example.com', password='testpassword')
        self.assertTrue(self.client.login(username='test@example.com', password='testpassword'))
        ReadLater.objects.create(user=self.user, news=self.news)
        response = self.client.post(reverse('news:remove_from_read_later', args=[self.news.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ReadLater.objects.filter(user=self.user, news=self.news).exists())

    def test_read_later_list_view(self):
        self.client.login(username='test@example.com', password='testpassword')
        self.assertTrue(self.client.login(username='test@example.com', password='testpassword'))
        ReadLater.objects.create(user=self.user, news=self.news)
        response = self.client.get(reverse('news:read_later_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test News')

# тесты форм
class CustomSignupFormTests(TestCase):

    def test_clean_username_valid(self):
        form = CustomSignupForm(data={
            'username': 'testuser',
            'password1': 'testpassword',
            'password2': 'testpassword',
            'email': 'testuser@example.com'
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['username'], 'testuser')

    def test_clean_username_invalid(self):
        form = CustomSignupForm(data={
            'username': '',
            'password1': 'testpassword',
            'password2': 'testpassword',
            'email': 'testuser@example.com'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_save_method(self):
        form = CustomSignupForm(data={
            'username': 'testuser',
            'password1': 'testpassword',
            'password2': 'testpassword',
            'email': 'testuser@example.com'
        })
        self.assertTrue(form.is_valid())

        request = Mock()
        request.session = {}

        user = form.save(request)
        self.assertEqual(user.username, 'testuser')

class EmailFormTests(TestCase):

    def test_email_form_valid(self):
        form = EmailForm(data={'email': 'test@example.com'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'test@example.com')

    def test_email_form_invalid(self):
        form = EmailForm(data={'email': 'invalid-email'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

# тест для парсера
class ParserTests(TestCase):

    @patch('news.parsers.requests.get')
    def test_parse_news(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.content = '''
        <rss>
            <item>
                <title>Test News</title>
                <link>https://example.com/test-news</link>
                <description>This is a test news content.</description>
                <pubDate>Wed, 22 Jan 2025 15:23:09 +0300</pubDate>
            </item>
        </rss>
        '''
        parse_news('https://example.com/rss/feed')
        self.assertTrue(News.objects.filter(title='Test News').exists())

# тест задачи
class TaskTests(TestCase):

    @patch('news.tasks.parse_news')
    def test_parse_news_task(self, mock_parse_news):
        parse_news_task('https://example.com/rss/feed')
        mock_parse_news.assert_called_once_with('https://example.com/rss/feed')
