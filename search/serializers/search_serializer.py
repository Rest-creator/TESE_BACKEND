# search/serializers.py
from rest_framework import serializers
from ..models import SearchIndexEntry

class SearchResultSerializer(serializers.ModelSerializer):
    """
    Serializes an index entry for the search results.
    (Implements SR-05)
    """
    # 'distance' is the annotated field from our query
    distance = serializers.FloatField(read_only=True)
    
    # 'content_object' is a GenericForeignKey. We need to serialize it
    # manually to show what object was found.
    found_object = serializers.SerializerMethodField()

    class Meta:
        model = SearchIndexEntry
        fields = [
            'title', 
            'description', 
            'metadata', 
            'distance', 
            'found_object'
        ]

    def get_found_object(self, obj: SearchIndexEntry) -> dict:
        # You can customize this. Maybe return a URL to the object.
        return {
            'type': obj.content_type.model,
            'id': obj.object_id,
            # This is slow! Better to have a 'get_absolute_url' on the model
            'representation': str(obj.content_object) 
        }