from rest_framework import viewsets, permissions

from modules.listings.service.service_services import ServiceService
from modules.listings.repository.service_repository import ServiceRepository
from modules.listings.serializer.service_serializer import ServiceSerializer
from teseapi.permissions import IsOwnerOrReadOnly


class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    queryset = ServiceRepository.get_all()

    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        images = self.request.FILES.getlist("images")
        return ServiceService.create_service(self.request.user, validated_data, images)

    def perform_update(self, serializer):
        service = serializer.instance
        return ServiceService.update_service(service, serializer.validated_data)

    def perform_destroy(self, instance):
        return ServiceService.delete_service(instance)


class MyServiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ServiceRepository.get_by_user(self.request.user)


class ActiveServiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.AllowAny]
    queryset = ServiceRepository.get_active()
