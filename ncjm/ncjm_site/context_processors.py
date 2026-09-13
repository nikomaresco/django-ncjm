from django.conf import settings


def analytics(request):
    """Expose only the public GA configuration needed by site templates."""
    return {
        "analytics": {
            "enabled": settings.GA_ENABLED,
            "measurement_id": settings.GA_MEASUREMENT_ID,
        }
    }
