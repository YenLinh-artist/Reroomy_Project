import json
import uuid

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from .models import (
    CustomerProfile,
    DanhMuc,
    Order,
    OrderItem,
    OrderNotification,
    SanPham,
    StaffNotification,
    StaffProfile,
)


class CustomerProductChangeFlowTests(TestCase):
    def setUp(self):
        self.category = DanhMuc.objects.create(ten_danh_muc="Đồ decor")
        self.old_product = SanPham.objects.create(
            ten_san_pham="Đèn cũ", gia_ban=10000, danh_muc=self.category, so_luong=5,
        )
        self.new_product = SanPham.objects.create(
            ten_san_pham="Đèn mới", gia_ban=10000, danh_muc=self.category, so_luong=5,
        )

    def make_order(self, customer=None):
        customer = customer or CustomerProfile.objects.create(full_name="Khách vãng lai")
        order = Order.objects.create(
            code=f"RR-{uuid.uuid4().hex[:10].upper()}", customer=customer,
            total=30000, shipping_address="Địa chỉ test",
        )
        item = OrderItem.objects.create(
            order=order, product=self.old_product, product_name=self.old_product.ten_san_pham,
            unit_price=self.old_product.gia_ban, quantity=1,
        )
        return order, item

    def request_change(self, order, item):
        return self.client.post(
            reverse("theo_doi_don_hang", args=[order.tracking_token]),
            {"action": "request_product_change", f"product_{item.pk}": str(self.new_product.pk)},
        )

    def test_guest_can_choose_replacement_product(self):
        order, item = self.make_order()

        page = self.client.get(reverse("theo_doi_don_hang", args=[order.tracking_token]))
        self.assertContains(page, f'name="product_{item.pk}"')
        self.assertContains(page, self.new_product.ten_san_pham)

        response = self.request_change(order, item)

        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertTrue(order.product_change_requested)
        self.assertEqual(
            json.loads(order.product_change_requested_items),
            {str(item.pk): str(self.new_product.pk)},
        )

    def test_logged_in_customer_can_choose_replacement_product(self):
        user = User.objects.create_user(username="customer", password="test-password-123")
        customer = CustomerProfile.objects.create(user=user, full_name="Khách có tài khoản")
        order, item = self.make_order(customer)
        self.client.force_login(user)

        response = self.request_change(order, item)

        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertTrue(order.product_change_requested)
        self.assertEqual(json.loads(order.product_change_requested_items), {str(item.pk): str(self.new_product.pk)})

    def test_customer_cannot_choose_product_with_different_price(self):
        order, item = self.make_order()
        higher_price = SanPham.objects.create(
            ten_san_pham="Đèn giá khác", gia_ban=12000, danh_muc=self.category, so_luong=5,
        )

        response = self.client.post(
            reverse("theo_doi_don_hang", args=[order.tracking_token]),
            {"action": "request_product_change", f"product_{item.pk}": str(higher_price.pk)},
        )

        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertFalse(order.product_change_used)
        self.assertFalse(order.product_change_requested)

    def test_cskh_approves_customer_choice_then_sales_confirms(self):
        order, item = self.make_order()
        self.request_change(order, item)
        sales = User.objects.create_user(username="sales", password="test-password-123", is_staff=True)
        StaffProfile.objects.create(user=sales, role=StaffProfile.Role.SALES)
        self.client.force_login(sales)
        dashboard = self.client.get(reverse("ban_hang_dashboard"))
        self.assertEqual(dashboard.context["new_order_count"], 0)
        sales_orders = self.client.get(reverse("ban_hang_don_hang"))
        self.assertNotContains(sales_orders, order.code)

        cskh = User.objects.create_user(username="cskh", password="test-password-123", is_staff=True)
        StaffProfile.objects.create(user=cskh, role=StaffProfile.Role.CONSULTANT)
        self.client.force_login(cskh)

        page = self.client.get(reverse("cskh_don_hang"))
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context["orders"][0].items.all()[0].customer_requested_product_id, str(self.new_product.pk))
        response = self.client.post(
            reverse("cskh_duyet_don_hang", args=[order.pk]),
            {f"product_{item.pk}": str(self.new_product.pk)},
        )
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(item.product_id, self.new_product.pk)
        self.assertTrue(order.product_change_pending_sales)
        self.assertEqual(order.status, Order.Status.PENDING)

        self.client.force_login(sales)
        dashboard = self.client.get(reverse("ban_hang_dashboard"))
        self.assertEqual(dashboard.context["new_order_count"], 1)
        sales_orders = self.client.get(reverse("ban_hang_don_hang"))
        self.assertContains(sales_orders, order.code)

        admin = User.objects.create_user(username="admin", password="test-password-123", is_staff=True)
        StaffProfile.objects.create(user=admin, role=StaffProfile.Role.ADMIN)
        self.client.force_login(sales)
        response = self.client.post(
            reverse("ban_hang_cap_nhat_don", args=[order.pk]),
            {"action": "confirm"},
        )

        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertFalse(order.product_change_pending_sales)
        self.assertTrue(OrderNotification.objects.filter(order=order, message__contains="cập nhật lại sản phẩm thành công").exists())
        self.assertTrue(StaffNotification.objects.filter(user=admin, order=order, message__contains="được duyệt sau khi đổi sản phẩm").exists())

        self.assertTrue(StaffNotification.objects.filter(user=cskh, order=order).exists())
        self.client.force_login(cskh)
        cskh_page = self.client.get(reverse("cskh_don_hang"))
        self.assertEqual(len(cskh_page.context["staff_notifications"]), 1)
        self.assertContains(cskh_page, order.code)


    def test_admin_is_notified_when_sales_confirms_regular_order(self):
        order, _ = self.make_order()
        sales = User.objects.create_user(username="sales-regular", password="test-password-123", is_staff=True)
        StaffProfile.objects.create(user=sales, role=StaffProfile.Role.SALES)
        admin = User.objects.create_user(username="admin-regular", password="test-password-123", is_staff=True)
        StaffProfile.objects.create(user=admin, role=StaffProfile.Role.ADMIN)
        self.client.force_login(sales)

        response = self.client.post(
            reverse("ban_hang_cap_nhat_don", args=[order.pk]),
            {"action": "confirm"},
        )

        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertTrue(StaffNotification.objects.filter(user=admin, order=order).exists())
        self.client.force_login(admin)
        admin_orders = self.client.get(reverse("quan_tri_don_hang"))
        self.assertEqual(len(admin_orders.context["product_change_notifications"]), 1)

    def test_demo_catalog_is_selectable_when_inventory_is_empty(self):
        self.old_product.delete()
        self.new_product.delete()
        order = Order.objects.create(
            code=f"RR-{uuid.uuid4().hex[:10].upper()}",
            customer=CustomerProfile.objects.create(full_name="Khách demo"),
            total=220000, shipping_address="Địa chỉ test",
        )
        item = OrderItem.objects.create(
            order=order, product_name="Gối ôm Chii kawa", unit_price=200000, quantity=1,
        )
        page = self.client.get(reverse("theo_doi_don_hang", args=[order.tracking_token]))
        self.assertContains(page, "Đèn có học")
        response = self.client.post(
            reverse("theo_doi_don_hang", args=[order.tracking_token]),
            {"action": "request_product_change", f"product_{item.pk}": "lamp"},
        )
        self.assertEqual(response.status_code, 302)

        cskh = User.objects.create_user(username="cskh-demo", password="test-password-123", is_staff=True)
        StaffProfile.objects.create(user=cskh, role=StaffProfile.Role.CONSULTANT)
        self.client.force_login(cskh)
        page = self.client.get(reverse("cskh_don_hang"))
        self.assertEqual(page.context["orders"][0].items.all()[0].customer_requested_product_id, "lamp")
        self.client.post(
            reverse("cskh_duyet_don_hang", args=[order.pk]),
            {f"product_{item.pk}": "lamp"},
        )
        item.refresh_from_db()
        self.assertEqual(item.product_name, "Đèn có học")
        self.assertIsNone(item.product_id)

        sales = User.objects.create_user(username="sales-demo", password="test-password-123", is_staff=True)
        StaffProfile.objects.create(user=sales, role=StaffProfile.Role.SALES)
        self.client.force_login(sales)
        response = self.client.post(
            reverse("ban_hang_cap_nhat_don", args=[order.pk]),
            {"action": "confirm"},
        )
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)

class GuestOrderNotificationsTests(TestCase):
    def test_tracking_visit_saves_guest_order_for_homepage_bell(self):
        customer = CustomerProfile.objects.create(full_name="Kh\u00e1ch v\u00e3ng lai")
        order = Order.objects.create(
            code=f"RR-{uuid.uuid4().hex[:10].upper()}", customer=customer,
            total=200000, shipping_address="\u0110\u1ecba ch\u1ec9 test",
        )
        OrderItem.objects.create(
            order=order, product_name="S\u1ea3n ph\u1ea9m test", unit_price=200000, quantity=1,
        )
        OrderNotification.objects.create(order=order, message="\u0110\u00e3 ti\u1ebfp nh\u1eadn \u0111\u01a1n h\u00e0ng.")

        self.client.get(reverse("theo_doi_don_hang", args=[order.tracking_token]))
        home = self.client.get(reverse("trang_chu"))
        self.assertContains(home, reverse("don_hang_khach_vang_lai"))
        self.assertGreater(home.context["guest_order_unread_count"], 0)

        bell = self.client.get(reverse("thong_bao_don_hang"))
        self.assertEqual(bell.status_code, 200)
        bell_item = bell.json()["notifications"][0]
        self.assertIn(order.code, bell_item["message"])
        self.assertEqual(bell_item["url"], reverse("theo_doi_don_hang", args=[order.tracking_token]))

        notifications = self.client.get(reverse("don_hang_khach_vang_lai"))
        self.assertContains(notifications, order.code)
        self.assertContains(notifications, reverse("theo_doi_don_hang", args=[order.tracking_token]))
        self.assertContains(notifications, "M\u1edf theo d\u00f5i \u0111\u01a1n")
        self.assertEqual(OrderNotification.objects.filter(order=order, is_read=False).count(), 0)
