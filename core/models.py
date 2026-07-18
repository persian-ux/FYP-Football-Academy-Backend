from django.db import models
from django.utils import timezone


class User(models.Model):
    class Role(models.TextChoices):
        player = "player"
        coach = "coach"
        admin = "admin"

    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=Role.choices)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.email


class Player(models.Model):
    class Sport(models.TextChoices):
        football = "football"
        cricket = "cricket"
        martial_arts = "martial_arts"
        swimming = "swimming"

    # users -> players is 1-to-1
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column="user_id")
    full_name = models.CharField(max_length=100, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    sport = models.CharField(max_length=20, choices=Sport.choices, blank=True, null=True)
    stats = models.JSONField(blank=True, null=True)

    def __str__(self) -> str:
        return self.full_name or f"Player({self.user.email})"


class Coach(models.Model):
    # users -> coaches is 1-to-1
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column="user_id")
    full_name = models.CharField(max_length=100, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    availability = models.JSONField(blank=True, null=True)

    def __str__(self) -> str:
        return self.full_name or f"Coach({self.user.email})"


class Session(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, db_column="coach_id")
    sport = models.CharField(max_length=50)
    date = models.DateTimeField()
    location = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"Session({self.sport} @ {self.location})"


class Match(models.Model):
    sport = models.CharField(max_length=50)
    team_a = models.CharField(max_length=100)
    team_b = models.CharField(max_length=100)
    score = models.CharField(max_length=20)
    date = models.DateTimeField()
    location = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"{self.team_a} vs {self.team_b}"


class Fee(models.Model):
    class Status(models.TextChoices):
        pending = "pending"
        paid = "paid"
        overdue = "overdue"

    player = models.ForeignKey(Player, on_delete=models.CASCADE, db_column="player_id")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.pending)
    due_date = models.DateField(blank=True, null=True)

    def __str__(self) -> str:
        return f"Fee({self.player_id}) - {self.status}"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages", db_column="sender_id")
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_messages",
        db_column="receiver_id",
    )
    content = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Message({self.sender_id} -> {self.receiver_id})"


class Announcement(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, db_column="coach_id")
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.title


class Notification(models.Model):
    class Type(models.TextChoices):
        email = "email"
        whatsapp = "whatsapp"
        system = "system"

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    message = models.TextField()
    type = models.CharField(max_length=10, choices=Type.choices)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Notification({self.type}) for {self.user_id}"

