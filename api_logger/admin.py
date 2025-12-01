from django.contrib import admin
from .models import APILog

@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = ('method', 'endpoint', 'status_code', 'timestamp', 'execution_time')
    list_filter = ('method', 'status_code', 'timestamp')
    search_fields = ('endpoint', 'response_body')
    readonly_fields = ('timestamp',)