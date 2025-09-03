# academies/choices.py
from django.db import models

class SportType(models.TextChoices):
    FOOTBALL      = "football", "Football"
    BASKETBALL    = "basketball", "Basketball"
    VOLLEYBALL    = "volleyball", "Volleyball"
    TENNIS        = "tennis", "Tennis"
    TABLE_TENNIS  = "table_tennis", "Table Tennis"
    SWIMMING      = "swimming", "Swimming"
