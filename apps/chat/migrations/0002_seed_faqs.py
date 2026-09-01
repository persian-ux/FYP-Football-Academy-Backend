"""Seed the six predefined FAQ entries used by the public chatbot.

The entries can be edited later from Django Admin without changing code.
"""

from django.db import migrations

DEFAULT_FAQS = [
    {
        "order": 1,
        "question": "Where is SportSphere Academy located?",
        "answer": "SportSphere Academy is located at the University of Lahore.",
    },
    {
        "order": 2,
        "question": "What are the academy training timings?",
        "answer": (
            "Our academy is open for training from Monday to Saturday, "
            "8:00 AM to 8:00 PM."
        ),
    },
    {
        "order": 3,
        "question": "How can I register or join the academy?",
        "answer": (
            "You can register through our website by creating a user account. "
            "If you would like to visit the academy in person, you can come to "
            "our location at the University of Lahore."
        ),
    },
    {
        "order": 4,
        "question": "What age groups can join the academy?",
        "answer": (
            "Our training is designed for young football players from "
            "approximately 4 to 19 years of age, covering early childhood "
            "through the teenage level."
        ),
    },
    {
        "order": 5,
        "question": "How can I contact SportSphere Academy?",
        "answer": (
            "You can contact SportSphere Academy through WhatsApp at +1 (555) 021-4001 "
            "or by email at [sportssphereacademy@gmail.com]"
            "(mailto:sportssphereacademy@gmail.com). Our academy operating hours are "
            "Monday to Saturday, 8:00 AM to 8:00 PM."
        ),
    },
    {
        "order": 6,
        "question": "What football training programs does the academy offer?",
        "answer": (
            "Our football training covers a wide range of skills and playing "
            "positions, including dribbling, striker/forward training, central "
            "midfield, defense, and other football positions. Players can develop "
            "their technical skills and learn the responsibilities and techniques "
            "associated with different positions."
        ),
    },
]


def seed_faqs(apps, schema_editor):
    FAQEntry = apps.get_model("chat", "FAQEntry")
    for item in DEFAULT_FAQS:
        FAQEntry.objects.get_or_create(
            question=item["question"],
            defaults={"answer": item["answer"], "order": item["order"], "is_active": True},
        )


def unseed_faqs(apps, schema_editor):
    FAQEntry = apps.get_model("chat", "FAQEntry")
    FAQEntry.objects.filter(
        question__in=[item["question"] for item in DEFAULT_FAQS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_faqs, unseed_faqs),
    ]