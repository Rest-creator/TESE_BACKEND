from rest_framework import viewsets, permissions
from modules.listings.service.supplier_service import SupplierProductService
from modules.listings.serializer.supplier_serializer import SupplierProductSerializer
from teseapi.models import SupplierProduct
from teseapi.permissions import IsOwnerOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response


class SupplierProductViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = SupplierProduct.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        """
        Custom create method that saves the product instance and handles image uploads.
        """
        # Call the service to create the product and get the instance back
        product_instance = SupplierProductService.create(
            user=self.request.user,
            validated_data=serializer.validated_data,
            files=self.request.FILES.getlist('images')
        )
        
        # After the instance is created, you must assign it to the serializer
        # so it can be used for to_representation.
        serializer.instance = product_instance

    def perform_update(self, serializer):
        SupplierProductService.update(
            instance=serializer.instance,
            validated_data=serializer.validated_data,
            files=self.request.FILES.getlist('images')
        )

    def perform_destroy(self, instance):
        SupplierProductService.delete(instance)
        
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_supplies(self, request):
        queryset = SupplierProduct.objects.filter(user=request.user).order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    # 3️⃣ Public endpoint — homepage supplies (no authentication required)
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def all_supplies(self, request):
        queryset = SupplierProduct.objects.all().order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
