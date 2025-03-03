import base64

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from apps.common.models import BaseModel


class Transaction(BaseModel):
    class StatusType(models.TextChoices):
        PENDING = 'pending', _('Pending')
        ACCEPTED = 'accepted', _('Accepted')
        REJECTED = 'rejected', _('Rejected')
        CANCELED = 'canceled', _('Canceled')

    class PaymentType(models.TextChoices):
        CARD = 'CARD', _('CARD')
        PAYLOV = 'PAYLOV', _('PAYLOV')

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transactions')
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    status = models.CharField(_('Status'), max_length=32, choices=StatusType.choices, default=StatusType.PENDING)
    remote_id = models.CharField(_('Remote id'), max_length=255, null=True, blank=True)
    tax_amount = models.DecimalField(_('TAX Amount'), max_digits=10, decimal_places=2, default=0.0, null=True,
                                     blank=True)
    paid_at = models.DateTimeField(verbose_name=_("Paid at"), null=True, blank=True)
    canceled_at = models.DateTimeField(verbose_name=_("Canceled at"), null=True, blank=True)
    payment_type = models.CharField(_("Payment Type"), choices=PaymentType.choices)
    extra = models.JSONField(_('Extra'), null=True, blank=True)
    is_notification_sent = models.BooleanField(_('Is notification sent'), default=False)

    class Meta:
        db_table = 'Transaction'
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ('remote_id',)

    def __str__(self):
        return f"{self.payment_type} | {self.id}"

    def success_process(self):
        self.status = self.StatusType.ACCEPTED
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at'])

        # self.user.update_balance()

    def cancel_process(self):
        self.status = self.StatusType.CANCELED
        self.canceled_at = timezone.now()
        self.save(update_fields=['status', 'canceled_at'])

        # self.user.update_balance()

    @property
    def payment_url(self):
        payment_url = ""

        if self.payment_type == Transaction.PaymentType.PAYLOV:
            merchant_id = settings.PAYMENT_CREDENTIALS['paylov']['merchant_id']
            query = f"merchant_id={merchant_id}&amount={self.amount}&account.order_id={self.id}"
            encode_params = base64.b64encode(query.encode("utf-8"))
            encode_params = str(encode_params, "utf-8")
            payment_url = f"{settings.PAYMENT_CREDENTIALS['paylov']['callback_url']}/{encode_params}"

        return payment_url


class MerchantRequestLog(BaseModel):
    payment_type = models.CharField(max_length=50, verbose_name=_("Payment type"),
                                    choices=Transaction.PaymentType.choices)
    method_type = models.CharField(max_length=255, verbose_name=_('Method type'), null=True, blank=True)
    request_headers = models.TextField(verbose_name=_("Request Headers"), null=True)
    request_body = models.TextField(verbose_name=_("Request Body"), null=True)

    response_headers = models.TextField(verbose_name=_("Response Headers"), null=True)
    response_body = models.TextField(verbose_name=_("Response Body"), null=True)
    response_status_code = models.PositiveSmallIntegerField(verbose_name=_("Response status code"), null=True)
