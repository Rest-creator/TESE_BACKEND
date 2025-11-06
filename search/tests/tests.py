# search/tests.py
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from unittest.mock import patch, MagicMock
from teseapi.models import Listing # Import your indexable model
from ..models import SearchIndexEntry
from ..services import index_object
from ..repositories.search_repository import search_index

# A mock embedding provider that always returns a predictable vector
class MockEmbeddingProvider:
    def get_embedding(self, text: str) -> list[float]:
        if "test listing" in text.lower():
            return [0.1, 0.2, 0.3, 0.4] # Vector for "Test Listing"
        if "another item" in text.lower():
            return [0.5, 0.6, 0.7, 0.8] # Vector for "Another Item"
        if "search query" in text.lower():
            return [0.1, 0.2, 0.3, 0.3] # Vector for our search query (very close to Test Listing)
        return [0.0, 0.0, 0.0, 0.0] # Default vector

@patch('search.services.EMBEDDING_PROVIDER', new_callable=MockEmbeddingProvider)
class ServiceTests(TestCase):

    def setUp(self):
        # Create a sample object to be indexed
        self.listing = Listing.objects.create(
            name="Test Listing",
            details="This is a test.",
            price=100
        )

    def test_index_object_creates_entry(self, mock_provider: MagicMock):
        """Test that the index_object service creates a SearchIndexEntry."""
        self.assertEqual(SearchIndexEntry.objects.count(), 0)
        
        index_object(self.listing)
        
        self.assertEqual(SearchIndexEntry.objects.count(), 1)
        entry = SearchIndexEntry.objects.first()
        
        self.assertEqual(entry.title, "Test Listing")
        self.assertEqual(entry.content_object, self.listing)
        self.assertEqual(entry.metadata['price'], 100.0)
        
        # Check that it used the mock provider's vector
        self.assertEqual(entry.embedding, [0.1, 0.2, 0.3, 0.4])

@patch('search.repositories.EMBEDDING_PROVIDER', new_callable=MockEmbeddingProvider)
class RepositoryTests(TestCase):

    def setUp(self):
        # Create a few indexed items manually
        self.listing1 = Listing.objects.create(name="Test Listing", details="Item one", price=50)
        self.listing2 = Listing.objects.create(name="Another Item", details="Item two", price=200)

        # Manually create the index entries (since signals are mocked)
        self.entry1 = SearchIndexEntry.objects.create(
            content_object=self.listing1,
            title="Test Listing",
            description="Item one",
            metadata={'price': 50, 'type': 'listing'},
            embedding=[0.1, 0.2, 0.3, 0.4]
        )
        self.entry2 = SearchIndexEntry.objects.create(
            content_object=self.listing2,
            title="Another Item",
            description="Item two",
            metadata={'price': 200, 'type': 'listing'},
            embedding=[0.5, 0.6, 0.7, 0.8]
        )

    def test_semantic_search_finds_closest(self, mock_provider: MagicMock):
        """Test that semantic search returns the closest vector match."""
        
        # This query ("search query") is designed to be closest to "Test Listing"
        results = search_index(query="search query")
        
        self.assertEqual(results.count(), 2)
        # The first result should be entry1 (Test Listing)
        self.assertEqual(results.first(), self.entry1)

    def test_filter_query_metadata(self, mock_provider: MagicMock):
        """Test filtering by metadata (edge case from SR-09)."""
        
        # Filter for items with price < 100
        filters = {'metadata__price__lt': 100}
        results = search_index(query="search query", filters=filters)
        
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), self.entry1)

    def test_filter_query_no_results(self, mock_provider: MagicMock):
        """Test a filter combination that returns nothing."""
        filters = {'metadata__price__gt': 500}
        results = search_index(query="search query", filters=filters)
        
        self.assertEqual(results.count(), 0)

    def test_search_with_no_query(self, mock_provider: MagicMock):
        """Test that filters work even without a search query string."""
        filters = {'metadata__type': 'listing'}
        results = search_index(query=None, filters=filters)
        
        self.assertEqual(results.count(), 2)