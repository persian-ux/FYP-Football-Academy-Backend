from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import FAQEntry

EXPECTED_FAQS = {
    "Where is SportSphere Academy located?": "SportSphere Academy is located at the University of Lahore.",
    "What are the academy training timings?": (
        "Our academy is open for training from Monday to Saturday, "
        "8:00 AM to 8:00 PM."
    ),
    "How can I register or join the academy?": (
        "You can register through our website by creating a user account. "
        "If you would like to visit the academy in person, you can come to "
        "our location at the University of Lahore."
    ),
    "What age groups can join the academy?": (
        "Our training is designed for young football players from "
        "approximately 4 to 19 years of age, covering early childhood "
        "through the teenage level."
    ),
    "How can I contact SportSphere Academy?": (
        "You can contact SportSphere Academy through WhatsApp at +1 (555) 021-4001 "
        "or by email at [sportssphereacademy@gmail.com]"
        "(mailto:sportssphereacademy@gmail.com). Our academy operating hours are "
        "Monday to Saturday, 8:00 AM to 8:00 PM."
    ),
    "What football training programs does the academy offer?": (
        "Our football training covers a wide range of skills and playing "
        "positions, including dribbling, striker/forward training, central "
        "midfield, defense, and other football positions. Players can develop "
        "their technical skills and learn the responsibilities and techniques "
        "associated with different positions."
    ),
}


class FAQChatbotAPITests(APITestCase):
    """Public, unauthenticated access to the predefined FAQ chatbot endpoints."""

    def setUp(self):
        self.list_url = reverse("faq-list")

    def test_unauthenticated_user_can_list_all_questions(self):
        # No authentication is performed on this request.
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(payload["success"])
        questions = [item["question"] for item in payload["data"]]
        for expected in EXPECTED_FAQS:
            self.assertIn(expected, questions)
        self.assertGreaterEqual(len(questions), 6)

    def test_list_only_returns_questions_not_answers(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.json()["data"]:
            self.assertIn("question", item)
            self.assertNotIn("answer", item)

    def test_each_predefined_answer_is_correct(self):
        for question, answer in EXPECTED_FAQS.items():
            faq = FAQEntry.objects.get(question=question)
            url = reverse("faq-answer", kwargs={"pk": faq.pk})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json()["data"]["answer"], answer)

    def test_retrieve_returns_question_and_answer(self):
        faq = FAQEntry.objects.get(question="What are the academy training timings?")
        response = self.client.get(reverse("faq-detail", kwargs={"pk": faq.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]
        self.assertEqual(data["question"], faq.question)
        self.assertEqual(data["answer"], faq.answer)

    def test_missing_faq_returns_404(self):
        url = reverse("faq-answer", kwargs={"pk": 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inactive_faq_is_hidden_from_public_endpoints(self):
        faq = FAQEntry.objects.get(question="Where is SportSphere Academy located?")
        faq.is_active = False
        faq.save()

        list_response = self.client.get(self.list_url)
        questions = [item["question"] for item in list_response.json()["data"]]
        self.assertNotIn(faq.question, questions)

        answer_url = reverse("faq-answer", kwargs={"pk": faq.pk})
        answer_response = self.client.get(answer_url)
        self.assertEqual(answer_response.status_code, status.HTTP_404_NOT_FOUND)