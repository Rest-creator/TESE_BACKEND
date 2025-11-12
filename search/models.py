# search/models.py
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from pgvector.django import VectorField
from django.conf import settings

class SearchIndexEntry(models.Model):
    """
    Generic search index storage for any model.
    Stores both textual metadata and optional embeddings.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    embedding = VectorField(dimensions=768, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("content_type", "object_id")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.content_type})"


class QueryLog(models.Model):
    """
    Logs search queries for analysis.
    (Implements SR-02 and SR-13)
    """
    query_text = models.CharField(max_length=500)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    session_key = models.CharField(max_length=40, blank=True, null=True)
    results_found = models.PositiveIntegerField(default=0)
    latency_ms = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"'{self.query_text}' ({self.results_found} results)"