from django.db import transaction as db_transaction
from django.utils import timezone

from apps.payment.models import Transaction


class PaylovProvider:
    ORDER_NOT_FOUND = "303"
    ORDER_ALREADY_PAID = "201"
    INVALID_AMOUNT = "5"
    SERVER_ERROR = "3"

    SUCCESS = "0"
    SUCCESS_STATUS_TEXT = "OK"
    ERROR_STATUS_TEXT = "ERROR"

    def __init__(self, params):
        self.params = params
        self.code = self.SUCCESS
        self.error = False
        self.transaction = self.get_transaction()

    def check(self):
        if not self.transaction:
            return True, self.ORDER_NOT_FOUND
        if self.transaction.status != Transaction.StatusType.PENDING:
            return True, self.ORDER_ALREADY_PAID
        if self.transaction.amount != self.params["amount"]:
            return True, self.INVALID_AMOUNT

        return self.error, self.code

    def perform(self):
        if not self.params.get("account"):
            return
        if not self.params.get("amount"):
            return
        try:
            transaction = Transaction.objects.get(id=self.params["account"]["order_id"])
            user = transaction.user

            if transaction.status != Transaction.StatusType.PENDING:
                return True, self.ORDER_ALREADY_PAID

            if transaction.amount != self.params["amount"]:
                return True, self.INVALID_AMOUNT

            with db_transaction.atomic():
                transaction.status = Transaction.StatusType.ACCEPTED
                transaction.remote_id = self.params["transaction_id"]
                transaction.paid_at = timezone.now()
                transaction.save()

                # with db_transaction.atomic():
                #     user.balance += transaction.amount
                #     user.save(update_fields=["balance"])

            if transaction.status != Transaction.StatusType.ACCEPTED:
                return True, self.SERVER_ERROR

        except Transaction.DoesNotExist:
            return True, self.ORDER_NOT_FOUND

        return self.error, self.code

    def get_transaction(self):
        if not self.params.get("account"):
            return
        if not self.params.get("amount"):
            return
        try:
            transaction = Transaction.objects.get(id=self.params["account"]["order_id"])
            return transaction
        except Transaction.DoesNotExist:
            return
