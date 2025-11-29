import time
from django.core.management.base import BaseCommand
from products.models import Listing  # Adjust import based on your app name
from search.services.search_services import index_object

class Command(BaseCommand):
    help = 'Rebuilds the semantic search index for Listings'

    def handle(self, *args, **kwargs):
        listings = Listing.objects.all()
        total = listings.count()
        
        self.stdout.write(f"Found {total} listings to index...")

        for i, listing in enumerate(listings, 1):
            try:
                self.stdout.write(f"Indexing [{i}/{total}]: {listing.name}...", ending='')
                
                # Call the service we wrote earlier
                index_object(listing)
                
                self.stdout.write(self.style.SUCCESS("OK"))

                # CRITICAL: SLEEP TO RESPECT GEMINI FREE TIER
                # 15 requests per minute = 1 request every 4 seconds
                time.sleep(4.1) 

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"FAILED: {e}"))

        self.stdout.write(self.style.SUCCESS("Reindexing complete!"))