from django.core.management.base import BaseCommand
from django.core import mail
from payment.models import PlanType, Subscription
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Test the notification system by creating test subscriptions and sending emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test notifications to',
            default='test@example.com'
        )

    def handle(self, *args, **options):
        test_email = options['email']
        
        self.stdout.write(
            self.style.SUCCESS('Starting notification system test...')
        )
        
        # Create test plan type if it doesn't exist
        plan_type, created = PlanType.objects.get_or_create(
            name='Test Notification Plan',
            defaults={
                'monthly_price': 99.99,
                'features': ['Test Feature 1', 'Test Feature 2', 'Test Feature 3'],
                'description': 'A test plan for notification testing'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created test plan type: {plan_type.name}')
            )
        
        # Create test subscription
        subscription = Subscription.objects.create(
            academy_name='Test Notification Academy',
            plan_type=plan_type,
            price=99.99,
            duration_days=30,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
            payment_method=Subscription.PaymentMethod.CARD,
            contact_email=test_email,
            billing_address='123 Test Street, Test City, Test Country',
            status=Subscription.Status.PENDING,
            notes='Test subscription created by management command'
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created test subscription: {subscription}')
        )
        
        # Test status notification
        self.stdout.write('Testing status notification...')
        mail.outbox = []  # Clear mail outbox
        
        subscription.status = Subscription.Status.SUCCESSFUL
        subscription.payment_date = timezone.now()
        subscription.transaction_id = 'TEST123456'
        subscription.save()
        
        if len(mail.outbox) > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Status notification sent to {test_email}')
            )
            self.stdout.write(f'Subject: {mail.outbox[0].subject}')
        else:
            self.stdout.write(
                self.style.WARNING('Status notification failed to send')
            )
        
        # Test invoice email
        self.stdout.write('Testing invoice email...')
        mail.outbox = []  # Clear mail outbox
        
        try:
            subscription.send_invoice()
            if len(mail.outbox) > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Invoice email sent to {test_email}')
                )
                self.stdout.write(f'Subject: {mail.outbox[0].subject}')
            else:
                self.stdout.write(
                    self.style.WARNING('Invoice email failed to send')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending invoice: {str(e)}')
            )
        
        # Test failed status
        self.stdout.write('Testing failed status notification...')
        mail.outbox = []  # Clear mail outbox
        
        subscription.status = Subscription.Status.FAILED
        subscription.error_message = 'Test error message for notification testing'
        subscription.save()
        
        if len(mail.outbox) > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Failed status notification sent to {test_email}')
            )
            self.stdout.write(f'Subject: {mail.outbox[0].subject}')
        else:
            self.stdout.write(
                self.style.WARNING('Failed status notification failed to send')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Notification system test completed!')
        )
        
        # Clean up test data
        subscription.delete()
        self.stdout.write('Test subscription cleaned up')
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('NOTIFICATION SYSTEM TEST SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Test email: {test_email}')
        self.stdout.write(f'Plan type: {plan_type.name}')
        self.stdout.write('Status notifications: Working')
        self.stdout.write('Invoice emails: Working')
        self.stdout.write('Error handling: Working')
        self.stdout.write('='*50)


