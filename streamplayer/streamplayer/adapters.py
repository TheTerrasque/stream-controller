from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
import django.conf

class NoSignupAccountAdapter(DefaultAccountAdapter):

    def is_open_for_signup(self, request):
        """
        Not open for regular signup.
        """
        return django.conf.settings.ACCOUNT_ALLOW_REGISTRATION


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def is_open_for_signup(self, request, sociallogin):
        """
        Allow signup via social accounts.
        """
        return django.conf.settings.SOCIALACCOUNT_ALLOW_REGISTRATION