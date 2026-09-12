"""Middleware to enforce strict private no-cache headers on all API responses.
Prevents sensitive user/candidate data from being cached by browsers, proxies, CDNs,
or shared between different browser tabs/sessions.
"""


class PrivateNoCacheAPIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Apply strict no-cache headers to all API endpoints
        if request.path.startswith("/api/"):
            response["Cache-Control"] = "no-cache, no-store, must-revalidate, private, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
            
            # Ensure caches distinguish responses by Auth and Onboarding tokens
            vary_headers = response.get("Vary", "")
            tokens_to_vary = ["Authorization", "X-Onboarding-Token", "Accept", "Origin"]
            
            existing = [h.strip() for h in vary_headers.split(",") if h.strip()]
            for token in tokens_to_vary:
                if token not in existing:
                    existing.append(token)
            
            response["Vary"] = ", ".join(existing)

        return response
