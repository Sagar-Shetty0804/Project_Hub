from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST


@login_required
def inbox(request):
    return render(request, "notifications/inbox.html", {"items": request.user.notifications.all()[:100]})


@login_required
def open_notification(request, pk):
    item = get_object_or_404(request.user.notifications, pk=pk)
    item.is_read = True
    item.save(update_fields=["is_read"])
    if item.url and url_has_allowed_host_and_scheme(item.url, allowed_hosts={request.get_host()}):
        return redirect(item.url)
    return redirect("notifications:inbox")


@login_required
@require_POST
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.POST.get("next") or "notifications:inbox")
