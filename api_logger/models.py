from django.db import models

class APILog(models.Model):
    # Request Info
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10) # GET, POST, PUT, etc.
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_body = models.TextField(null=True, blank=True) # Be careful with passwords!
    
    # Response Info
    status_code = models.IntegerField()
    response_body = models.TextField(null=True, blank=True)
    execution_time = models.FloatField(help_text="Time taken in seconds")
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"