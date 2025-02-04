from django.shortcuts import render, redirect, get_object_or_404
from .models import News, CustomUser, ReadLater
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .forms import EmailForm
from django.urls import reverse
from allauth.account.views import LoginView, PasswordResetView
from allauth.account.models import EmailAddress
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse

@login_required
def news_list(request):
    cache_key = 'news_list'
    news = cache.get(cache_key)

    if not news:
        news = News.objects.all()
        cache.set(cache_key, news, 60 * 60)
        
    paginator = Paginator(news, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    read_later_ids = set(request.user.readlater_set.values_list('news_id', flat=True))
    return render(request, 'news/news_list.html', {'page_obj': page_obj,
                                                   'read_later_ids': read_later_ids,})

def no_link(request):
    return render(request, 'news/no_link.html')

# закладки для новостей (читать позже)
@login_required
@require_POST
def add_to_read_later(request, news_id):
    news = get_object_or_404(News, id=news_id)
    ReadLater.objects.get_or_create(user=request.user, news=news)
    cache.delete(f'read_later_list_{request.user.id}')
    return render(request, 'news/read_later_button.html', {'news': news, 'action': 'remove'})

@login_required
@require_POST
def remove_from_read_later(request, news_id):
    news = get_object_or_404(News, id=news_id)
    ReadLater.objects.filter(user=request.user, news=news).delete()

    # очистка кэша
    cache.delete(f'read_later_list_{request.user.id}')
    
    # проверяем, откуда пришёл запрос
    from_read_later = request.GET.get('from_read_later', 'false') == 'true'

    if from_read_later:
        # если запрос из read_later_list.html, возвращаем пустой HTML
        return HttpResponse('', content_type='text/html')
    else:
        # если запрос из news_list.html, возвращаем обновлённую кнопку
        return render(request, 'news/read_later_button.html', {'news': news, 'action': 'add'})

@login_required
def read_later_list(request):
    cache_key = f'read_later_list_{request.user.id}'
    read_later_items = cache.get(cache_key)

    if not read_later_items:
        read_later_items = ReadLater.objects.filter(user=request.user).select_related('news')
        cache.set(cache_key, read_later_items, 60 * 60)
    return render(request, 'news/read_later_list.html', {'read_later_items': read_later_items})

# AUTH
def first_page_login(request):
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid(): 
            email = form.cleaned_data['email']
            User = get_user_model()  # получаем модель пользователя

            try:
                user = User.objects.get(email=email)
                # проверяем, зарегистрирован ли пользователь через социальную сеть
                if user.social_auth.exists():
                    email_address = EmailAddress.objects.filter(user=user, email=email, verified=True).first()
                    if email_address:
                        return redirect(f"{reverse('account_login')}?email={email}")
                    else:
                        return redirect('password_reset_notification')
                return redirect(f"{reverse('account_login')}?email={email}")
            
            except User.DoesNotExist:
                error_message = 'Пользователь с таким email не найден'
                form.add_error('email', error_message)
    else:
        form = EmailForm()

    return render(request, 'account/first_page_login.html', {'form': form})


def password_reset_notification(request):
    return render(request, 'account/password_reset_notification.html')


class CustomLoginView(LoginView): # email сохраняется в форме
    def get(self, request, *args, **kwargs):
        email = request.GET.get('email', '')
        context = self.get_context_data()
        context['email'] = email
        return self.render_to_response(context)
    
    def form_invalid(self, form):
        email = self.request.POST.get('login', '')
        return self.render_to_response(self.get_context_data(form=form, email=email))
    
    def form_valid(self, form):
        email = form.cleaned_data.get('login') 
        user = CustomUser.objects.filter(email=email).first()

        if user is None:
            messages.error(self.request, "Пользователь с указанным email не найден.")
            return self.form_invalid(form)
        
        email_address = EmailAddress.objects.filter(email=email, verified=True).first()
        
        if email_address is None:
            messages.error(self.request, "Ваш email еще не подтвержден. Проверьте вашу почту.")
            return redirect('account_email_verification_sent')

        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        return super().form_valid(form)

class CustomPasswordResetView(PasswordResetView): # email сохраняется в форме
    def get(self, request, *args, **kwargs):
        email = request.GET.get('email', '')
        context = self.get_context_data()
        context['email'] = email
        return self.render_to_response(context)

    def form_invalid(self, form):
        email = self.request.POST.get('email', '')
        return self.render_to_response(self.get_context_data(form=form, email=email))