from django.apps import AppConfig


class PlayerPaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'player_payments'
    verbose_name = 'Player Payments'
    
    def ready(self):
      
        pass

