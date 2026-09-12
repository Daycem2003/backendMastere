from django.urls import path

from .views.activation_view import ActivateAccountView
from .views.login_view import IdNumberLoginView, LoginView, PhoneLoginView
from .views.otp_view import VerifyOtpView
from .views.password_view import PasswordForgotView, PasswordResetView
from .views.register_view import RegisterView
from .views.token_view import MeView, RefreshTokenView

urlpatterns = [
    path("register", RegisterView.as_view()), path("login", LoginView.as_view()),
    path("login/id-number", IdNumberLoginView.as_view()), path("login/phone", PhoneLoginView.as_view()),
    path("otp/verify", VerifyOtpView.as_view()), path("token/refresh", RefreshTokenView.as_view()),
    path("password/forgot", PasswordForgotView.as_view()), path("password/reset", PasswordResetView.as_view()),
    path("activate", ActivateAccountView.as_view()),
    path("me", MeView.as_view()),
]

