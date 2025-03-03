from django.urls import path

from apps.payment.api_endpoints import *  # noqa
from apps.payment.payment_types.paylov.merchant.views import *  # noqa


app_name = 'payment'

urlpatterns = [
    path("TransactionCreate/", TransactionCreateView.as_view(), name="transaction-create"),
    path("UserTransactionList/", TransactionListView.as_view(), name="transaction-list"),
    path("TransactionDetail/<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),


    path("paylov/", PaylovAPIView.as_view(), name="paylov"),
]