from django.http import JsonResponse


def dashboard_home(request):
    return JsonResponse({"status": "ok", "app": "dashboard"})
