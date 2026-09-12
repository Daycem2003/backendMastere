from django.urls import get_resolver


def test_authentication_routes_are_registered():
    routes = {str(pattern.pattern) for pattern in get_resolver().url_patterns[0].url_patterns}
    assert routes == {
        "register",
        "login",
        "login/id-number",
        "login/phone",
        "otp/verify",
        "token/refresh",
        "password/forgot",
        "password/reset",
        "activate",
        "me",
    }

