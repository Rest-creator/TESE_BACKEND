from django.core.management.base import BaseCommand
from teseapi.models import Listing
from search.embeddings import generate_embedding

class Command(BaseCommand):
    help = "Reindex all product embeddings"

    def handle(self, *args, **kwargs):
        for listing in Listing.objects.all():
            text = f"{listing.name} {listing.description}"
            listing.embedding = generate_embedding(text)
            listing.save()
        print("Reindexing complete.")
