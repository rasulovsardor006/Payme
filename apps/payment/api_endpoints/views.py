from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.payment.api_endpoints.permissions import IsOwner
from apps.payment.api_endpoints.serializers import TransactionCreateSerializer, TransactionDetailSerializer
from apps.payment.models import Transaction


class TransactionCreateView(generics.CreateAPIView):
    serializer_class = TransactionCreateSerializer
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionDetailSerializer
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user,
                                    status=Transaction.StatusType.ACCEPTED).order_by('-created_at')


class TransactionDetailView(generics.RetrieveAPIView):
    serializer_class = TransactionDetailSerializer
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated, IsOwner]


__all__ = ['TransactionCreateView', 'TransactionDetailView', 'TransactionListView']
