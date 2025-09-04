from django.core.management.base import BaseCommand
from academies.models import Academy
from payment.models import PlanType, SubscriptionPlan


class Command(BaseCommand):
    help = 'Create test SubscriptionPlan records for existing academies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--academy-slug',
            type=str,
            help='Create subscription plan for a specific academy (by slug)',
        )
        parser.add_argument(
            '--all-academies',
            action='store_true',
            help='Create subscription plans for all academies',
        )

    def handle(self, *args, **options):

        plan_type, created = PlanType.objects.get_or_create(
            name='Basic Plan',
            defaults={
                'description': 'Basic academy subscription plan',
                'monthly_price': 100.00,
                'yearly_price': 1000.00,
                'features': ['Access to all programs', 'Monthly progress reports', 'Parent dashboard'],
                'icon_class': 'bi-person-check',
                'is_featured': False,
                'display_order': 1,
            }
        )
        
        if created:
            self.stdout.write(f'Created plan type: {plan_type.name}')
        else:
            self.stdout.write(f'Using existing plan type: {plan_type.name}')


        if options['academy_slug']:
            try:
                academies = [Academy.objects.get(slug=options['academy_slug'])]
            except Academy.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Academy with slug "{options["academy_slug"]}" not found.')
                )
                return
        elif options['all_academies']:
            academies = Academy.objects.all()
        else:

            try:
                academies = [Academy.objects.get(slug='Falcon-Academy')]
            except Academy.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('Falcon Academy not found. Use --academy-slug or --all-academies.')
                )
                return

        if not academies:
            self.stdout.write(
                self.style.WARNING('No academies found.')
            )
            return

        created_count = 0
        updated_count = 0

        for academy in academies:
            self.stdout.write(f'Creating subscription plan for academy: {academy.name}')
            

            subscription_plan, created = SubscriptionPlan.objects.get_or_create(
                academy=academy,
                title=f'{academy.name} Basic Plan',
                defaults={
                    'plan_type': plan_type,
                    'price': 100.00,
                    'billing_type': 'monthly',
                    'description': f'Basic subscription plan for {academy.name}',
                    'program_features': ['Access to all programs', 'Monthly progress reports', 'Parent dashboard'],
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    f'  ✓ Created subscription plan: {subscription_plan.title} - SAR {subscription_plan.price}'
                )
            else:

                subscription_plan.is_active = True
                subscription_plan.price = 100.00
                subscription_plan.save()
                updated_count += 1
                self.stdout.write(
                    f'  ↻ Updated subscription plan: {subscription_plan.title} - SAR {subscription_plan.price}'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new subscription plans, '
                f'updated {updated_count} existing subscription plans.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                'Subscription plans are now available for parents to view and subscribe to.'
            )
        )
