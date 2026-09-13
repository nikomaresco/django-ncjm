from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@require_GET
@never_cache
def health(request):
    """Return a dependency-free liveness response for internal health checks."""
    return JsonResponse({"status": "ok"})
