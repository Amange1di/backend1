from core.models import AuditLog


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        parts = [part.strip() for part in forwarded.split(",") if part.strip()]
        if parts:
            return parts[-1]
    return request.META.get("REMOTE_ADDR") or None


def write_audit(
    request,
    *,
    action,
    obj=None,
    company=None,
    before=None,
    after=None,
    metadata=None,
):
    actor = getattr(request, "user", None)
    if not getattr(actor, "is_authenticated", False):
        actor = None

    if company is None and obj is not None:
        company = getattr(obj, "company", None)

    return AuditLog.objects.create(
        actor=actor,
        company=company,
        action=action,
        object_type=(
            obj.__class__.__name__
            if obj is not None
            else ""
        ),
        object_id=(
            str(getattr(obj, "pk", ""))
            if obj is not None
            else ""
        ),
        ip_address=_client_ip(request),
        before=before or {},
        after=after or {},
        metadata=metadata or {},
    )
