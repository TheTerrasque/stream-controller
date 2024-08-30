from django import forms
from django.contrib.auth.models import User
from player.models import Film, Stream

class NewAdminAccountForm(forms.Form):
    name = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', max_length=100, widget=forms.PasswordInput)

    def save(self):
        user = User.objects.create_user(self.cleaned_data['name'], "", self.cleaned_data['password'])
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user

class FilmForm(forms.ModelForm):
    guild_movie = forms.BooleanField(required=False, label="Is Next Guild Movie", help_text="If set, guild movie playlist will be cleared and this film will be added to it")
    class Meta:
        model = Film
        fields = ['video', "subtitle"]