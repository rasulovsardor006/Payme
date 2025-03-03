from django.conf import settings
from django.db import transaction as db_transaction
from drf_yasg.utils import swagger_auto_schema

from rest_framework.views import APIView
from rest_framework.response import Response

from apps.payment.models import MerchantRequestLog, Transaction
from apps.payment.payment_types.paylov.provider import PaylovProvider
from apps.payment.payment_types.paylov.merchant.auth import CustomBasicAuthentication
from apps.payment.payment_types.paylov.merchant.utils import PaylovMethods
from apps.payment.payment_types.paylov.merchant.serializers import PaylovSerializer


class PaymentView(APIView):
    authentication_classes = [
        CustomBasicAuthentication.from_settings(
            settings.PAYMENT_CREDENTIALS["paylov"]["username"], settings.PAYMENT_CREDENTIALS["paylov"]["password"]
        )
    ]
    PROVIDER: str = ""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # MerchantRequestLog.objects.create(
        #     request_headers=self.request.headers,
        #     request_body=self.request.data,
        #     method_type=self.request.method,
        #     response_body=response.data,
        #     response_status_code=response.status_code,
        #     payment_type=self.PROVIDER,
        # )
        return response


class PaylovAPIView(PaymentView):
    PROVIDER = Transaction.PaymentType.PAYLOV  # type: ignore

    def __init__(self):
        self.METHODS = {
            PaylovMethods.CHECK_TRANSACTION: self.check,
            PaylovMethods.PERFORM_TRANSACTION: self.perform,
        }
        self.params = None
        self.amount = None
        super(PaylovAPIView, self).__init__()

    @swagger_auto_schema(request_body=PaylovSerializer)
    def post(self, request, *args, **kwargs):
        serializer = PaylovSerializer(data=request.data, many=False)

        serializer.is_valid(raise_exception=True)

        method = serializer.validated_data["method"]
        self.params = serializer.validated_data["params"]

        with db_transaction.atomic():
            response_data = self.METHODS[method]()

        if isinstance(response_data, dict):
            response_data.update({"jsonrpc": "2.0", "id": request.data.get("id", None)})

        return Response(response_data)

    def check(self):
        error, code = PaylovProvider(self.params).check()
        if error:
            return dict(result=dict(status=code, statusText=PaylovProvider.ERROR_STATUS_TEXT))
        return dict(result=dict(status=code, statusText=PaylovProvider.SUCCESS_STATUS_TEXT))

    def perform(self):
        error, code = PaylovProvider(self.params).perform()
        # when order is not found
        if error and code == PaylovProvider.ORDER_NOT_FOUND:
            return dict(result=dict(status=code, statusText=PaylovProvider.ERROR_STATUS_TEXT))

        return dict(result=dict(status=code, statusText=PaylovProvider.SUCCESS_STATUS_TEXT))


__all__ = [
    'PaylovAPIView'
]
