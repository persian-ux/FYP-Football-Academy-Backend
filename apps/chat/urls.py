from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FAQEntryViewSet, chatbot_demo

router = DefaultRouter()
router.register(r"faqs", FAQEntryViewSet, basename="faq")

urlpatterns = [
    path("chatbot-demo/", chatbot_demo, name="chatbot-demo"),
    path("", include(router.urls)),
]
