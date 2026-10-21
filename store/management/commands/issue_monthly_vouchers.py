import calendar
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from store.services import BUSINESS_TIME_ZONE, issue_month_vouchers


class Command(BaseCommand):
    help = "Issue Thankyou vouchers at 23:59 Vietnam time on the last day of a month."

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            help="Manually process a month in YYYY-MM format (for a missed scheduled run).",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        local_now = timezone.localtime(now, BUSINESS_TIME_ZONE)

        if options["month"]:
            try:
                reward_month = datetime.strptime(options["month"], "%Y-%m").date().replace(day=1)
            except ValueError as exc:
                raise CommandError("--month phải có định dạng YYYY-MM.") from exc
        else:
            # Render starts the job at 23:59 local time. Allow a short startup delay
            # that can carry the process into the first few minutes of next month.
            if local_now.day == 1 and local_now.hour == 0 and local_now.minute <= 5:
                scheduled_date = local_now.date() - timedelta(days=1)
            elif local_now.hour == 23 and local_now.minute >= 59:
                scheduled_date = local_now.date()
            else:
                self.stdout.write("Chưa đến lịch tổng kết 23:59 ngày cuối tháng; bỏ qua lần chạy này.")
                return

            month_last_day = calendar.monthrange(scheduled_date.year, scheduled_date.month)[1]
            if scheduled_date.day != month_last_day:
                self.stdout.write("Hôm nay không phải ngày cuối tháng; bỏ qua lần chạy này.")
                return
            reward_month = scheduled_date.replace(day=1)

        count = issue_month_vouchers(reward_month, now=now)
        self.stdout.write(
            self.style.SUCCESS(
                f"Đã tổng kết {reward_month:%m/%Y}: {count} khách đủ điều kiện nhận voucher Thankyou."
            )
        )
