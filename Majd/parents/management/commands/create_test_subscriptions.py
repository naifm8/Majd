from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from parents.models import ParentSubscription
from accounts.models import ParentProfile
from academies.models import Academy


class Command(BaseCommand):
    help = 'Create test ParentSubscription records for existing parents and academies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--academy-slug',
            type=str,
            help='Create subscriptions for a specific academy (by slug)',
        )
        parser.add_argument(
            '--all-academies',
            action='store_true',
            help='Create subscriptions for all academies',
        )

    def handle(self, *args, **options):
 
        parents = ParentProfile.objects.all()
        
        if not parents.exists():
            self.stdout.write(
                self.style.WARNING('No parent profiles found. Please create some parents first.')
            )
            return


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
            self.stdout.write(f'Creating subscriptions for academy: {academy.name}')
            
            for parent in parents:

                subscription, created = ParentSubscription.objects.get_or_create(
                    parent=parent,
                    academy=academy,
                    defaults={
                        'is_active': True,
                        'start_date': timezone.now(),
                        'end_date': timezone.now() + timedelta(days=30),
                        'subscription_type': 'monthly',
                        'amount_paid': 100.00,  
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        f'  ✓ Created subscription for {parent.user.username}'
                    )
                else:

                    subscription.is_active = True
                    subscription.end_date = timezone.now() + timedelta(days=30)
                    subscription.save()
                    updated_count += 1
                    self.stdout.write(
                        f'  ↻ Updated subscription for {parent.user.username}'
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new subscriptions, '
                f'updated {updated_count} existing subscriptions.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                'Parents can now enroll their children in academy programs.'
            )
        )
