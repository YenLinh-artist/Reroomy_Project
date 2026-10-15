def admin_role(request):
    if not request.user.is_authenticated:
        return {"role": ""}
    if request.user.is_superuser:
        return {"role": "admin"}
    try:
        return {"role": request.user.staff_profile.role if request.user.staff_profile.is_enabled else ""}
    except Exception:
        return {"role": ""}


def admin_notifications(request):
    if not request.user.is_authenticated:
        return {"admin_notification_count": 0}
    try:
        if request.user.is_superuser or (request.user.is_staff and request.user.staff_profile.is_enabled and request.user.staff_profile.role in ("admin", "sales")):
            from .models import Order
            return {"admin_notification_count": Order.objects.filter(status=Order.Status.PENDING).count()}
        if request.user.is_staff and request.user.staff_profile.is_enabled and request.user.staff_profile.role == "consultant":
            from .models import DecorConsultation
            return {"admin_notification_count": DecorConsultation.objects.filter(assigned_to=request.user, status__in=["new", "assigned", "working"]).count()}
    except Exception:
        pass
    return {"admin_notification_count": 0}
