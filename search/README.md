# **Semantic Search Module for Django**

A plug-and-play **semantic search module** for Django applications that allows you to index models, store vector embeddings, and perform semantic search. Works with **pgvector/PostgreSQL**, supports dynamic indexing, and provides a **REST API** via Django REST Framework.

---

## **Features**

* Plug-and-play: Add `to_search_document()` to any model to make it searchable.
* Stores **vector embeddings** for semantic search.
* Supports **dynamic indexing** and **reindexing** per model.
* Provides **REST API endpoints** for search, indexing, and admin management.
* Fallback search with plain text filtering for SQLite or environments without vector support.
* Compatible with any Django model and multi-tenant apps.

---

## **Installation**

1. Install dependencies:

```bash
pip install django djangorestframework psycopg2-binary django-pgvector
```

2. Add apps to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "pgvector",
    "search",
]
```

3. Apply migrations:

```bash
python manage.py makemigrations search
python manage.py migrate
```

---

## **Model Setup**

### **1. Add `to_search_document()` to any model**

```python
class Listing(models.Model):
    ...
    def to_search_document(self):
        first_image = self.images.first().image_url if self.images.exists() else ""
        return {
            "id": self.id,
            "name": self.name,
            "price": float(self.price),
            "unit": self.unit,
            "image": first_image,
            "category": self.category or "",
            "seller": self.user.username,
            "sellerId": self.user_id,
            "location": self.location,
            "description": self.description or "",
            "status": self.status or "",
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "embedding": None,  # Generated automatically by the search module
        }
```

### **2. SearchIndexEntry model**

```python
from pgvector.models import VectorField
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

class SearchIndexEntry(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict)
    embedding = VectorField(dim=384, default=list)  # store vector

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("content_type", "object_id")
```

---

## **Core Services**

### **Indexing an object**

```python
from search.services.search_services import index_object

index_object(instance)  # instance is any model with `to_search_document()`
```

* Automatically generates embeddings using `generate_embedding()`.
* Creates or updates the `SearchIndexEntry`.

### **Deleting an object from the index**

```python
from search.services.search_services import delete_object_from_index

delete_object_from_index(instance)
```

* Removes the indexed object safely from the search index.

### **Vector search**

```python
from search.services.search_services import search_by_vector

results = search_by_vector("fresh organic peas")
for entry in results:
    print(entry.title, entry.metadata)
```

* Returns the most semantically similar entries based on embeddings.
* Supports filtering by metadata fields or content type.

---

## **Django REST API**

### **Search Endpoint**

* **GET `/search/`**
* Query parameters:

  * `q` → search query
  * `metadata__<field>` → filter by metadata key
  * `type` → filter by model type

```http
GET /search/?q=fresh%20peas&metadata__category=Vegetables&type=listing
```

### **Admin Indexing Endpoint**

* **POST `/search/index/`** → index a single object

```json
{
  "app_label": "listings",
  "model_name": "listing",
  "object_id": 123
}
```

* **DELETE `/search/index/{id}/`** → remove a single SearchIndexEntry
* **POST `/search/rebuild/`** → rebuild the entire index for a model

```json
{
  "app_label": "listings",
  "model_name": "listing"
}
```

> **Note:** Rebuilding should ideally be run as a background task for large datasets.

---

## **Plug-and-Play Integration**

1. Add the module to any Django project.
2. Define `to_search_document()` on models to be indexed.
3. Call `index_object(instance)` after creating/updating objects.
4. Use `search_by_vector(query)` to perform semantic search.
5. Optionally expose the REST endpoints for search and admin tasks.

---

## **Example Usage**

```python
# Index a new listing
listing = Listing.objects.first()
index_object(listing)

# Perform a semantic search
results = search_by_vector("organic vegetables for sale")
for r in results:
    print(r.title, r.metadata)

# Delete an object from the index
delete_object_from_index(listing)
```

---

