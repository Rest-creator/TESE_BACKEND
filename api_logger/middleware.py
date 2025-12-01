import time
from django.http import JsonResponse
from django.core.exceptions import RequestDataTooBig
from .models import APILog

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Capture request start time
        start_time = time.time()
        
        request_body = ""
        
        # --- FIX STARTS HERE ---
        # We wrap the body access in a try/except block to catch the overflow error
        try:
            if request.body:
                try:
                    request_body = request.body.decode('utf-8')
                    
                    if "password" in request_body.lower():
                        request_body = "SENSITIVE_DATA_REDACTED"
                except UnicodeDecodeError:
                    request_body = "Binary Data"
                    
        except RequestDataTooBig:
            # 2. Return a proper JSON error immediately
            # We return 413 (Payload Too Large) so the frontend knows exactly what failed
            return JsonResponse({
                "error": "Payload Too Large",
                "message": "The uploaded file exceeds the maximum allowed size.",
                "code": "file_too_large"
            }, status=413)
        # --- FIX ENDS HERE ---

        # 3. Process the request (Call the view)
        response = self.get_response(request)

        # 4. Calculate execution time
        duration = time.time() - start_time

        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return response

        # 6. Capture response body (if it's JSON)
        response_body = ""
        if 'application/json' in response.get('Content-Type', ''):
            try:
                response_body = response.content.decode('utf-8')
            except:
                response_body = "Could not decode"

        # 7. Save to Database
        # Note: If the file was too big, we returned early above, so we don't log it here 
        # to save DB space and processing time. 
        APILog.objects.create(
            endpoint=request.path,
            method=request.method,
            ip_address=self.get_client_ip(request),
            request_body=request_body,
            status_code=response.status_code,
            response_body=response_body,
            execution_time=duration,
            error_message=response.reason_phrase if response.status_code >= 400 else None
        )

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip