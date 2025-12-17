from allauth.account.views import SignupView
from django.shortcuts import redirect
from django.contrib import messages

class CustomSignupView(SignupView):
    def form_valid(self, form):
        # Save the user but do NOT log them in
        self.user, resp = form.try_save(self.request)
        if resp:
            return resp
        messages.success(self.request, 'Account created successfully! Please sign in with your new credentials.')
        return redirect('account_login')
