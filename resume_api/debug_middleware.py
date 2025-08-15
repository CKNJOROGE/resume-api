# resume_api/debug_middleware.py

class DebugRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("--- DEBUG MIDDLEWARE ---")
        print(f"Host: {request.get_host()}")
        print(f"Origin Header: {request.headers.get('Origin')}")
        print(f"Referer Header: {request.headers.get('Referer')}")
        print(f"X-Forwarded-Proto Header: {request.headers.get('X-Forwarded-Proto')}")
        print("----------------------")

        response = self.get_response(request)
        return response