from django.http import JsonResponse


def home(request):
	return JsonResponse({"message": "Football Academy Backend is running"})


def health_check(request):
	return JsonResponse({"status": "ok", "service": "football-academy-backend"})
