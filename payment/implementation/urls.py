from rest_framework.routers import DefaultRouter
from .payment_views import CartViewSet, CheckoutViewSet

router = DefaultRouter()
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"checkout", CheckoutViewSet, basename="checkout")

urlpatterns = router.urls
