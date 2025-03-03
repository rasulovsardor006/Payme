from rest_framework import serializers

from apps.payment.payment_types.paylov.merchant.utils import PaylovMethods


class PaylovSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    method = serializers.ChoiceField(choices=PaylovMethods.choices())
    params = serializers.JSONField()
