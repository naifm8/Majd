from django.core.management.base import BaseCommand
from academies.models import Academy
from payment.models import PlanType, SubscriptionPlan
from accounts.models import ParentProfile


class Command(BaseCommand):
    help = 'Debug database content for payments page'

    def handle(self, *args, **options):
        self.stdout.write("=== DATABASE DEBUG INFO ===")
        

        academies = Academy.objects.all()
        self.stdout.write(f"Academies found: {academies.count()}")
        for academy in academies:
            self.stdout.write(f"  - {academy.name} (slug: {academy.slug})")
        

        plan_types = PlanType.objects.all()
        self.stdout.write(f"\nPlan Types found: {plan_types.count()}")
        for plan_type in plan_types:
            self.stdout.write(f"  - {plan_type.name} (monthly: {plan_type.monthly_price})")
        

        subscription_plans = SubscriptionPlan.objects.all()
        self.stdout.write(f"\nSubscription Plans found: {subscription_plans.count()}")
        for plan in subscription_plans:
            self.stdout.write(f"  - {plan.title} for {plan.academy.name} (price: {plan.price}, active: {plan.is_active})")
        

        parents = ParentProfile.objects.all()
        self.stdout.write(f"\nParent Profiles found: {parents.count()}")
        for parent in parents:
            self.stdout.write(f"  - {parent.user.username} ({parent.user.email})")
        
        self.stdout.write("\n=== END DEBUG INFO ===")
