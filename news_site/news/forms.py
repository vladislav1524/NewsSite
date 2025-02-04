from django import forms 
from django.core.exceptions import ValidationError
from allauth.account.forms import SignupForm

# auth
class CustomSignupForm(SignupForm):
    username = forms.CharField(max_length=150, label='Username')

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if not username:
            raise ValidationError("Enter your username.")

        return username
    
    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.username = self.cleaned_data['username']
        user.save()
        return user
    

class EmailForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254)
