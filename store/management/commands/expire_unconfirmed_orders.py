from django.core.management.base import BaseCommand

from store.services import expire_unconfirmed_cod_orders


class Command(BaseCommand):
    help = "Cancel COD orders that have remained unconfirmed for three days."

    def handle(self, *args, **options):
        count = expire_unconfirmed_cod_orders()
        self.stdout.write(self.style.SUCCESS(f"Đã tự hủy {count} đơn COD quá hạn."))
