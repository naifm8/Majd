from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from parents.models import Child, Enrollment
from player_payments.models import PlayerEnrollment, PaymentTransaction, PlayerSubscription
from academies.models import Academy, Program
from accounts.models import ParentProfile
from parents.utils import send_payment_invoice_email
from datetime import date, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Test the invoice email functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test invoice to',
            default='test@example.com'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f'Testing invoice email to: {email}')
        
        try:

            user, created = User.objects.get_or_create(
                username='test_parent',
                defaults={
                    'email': email,
                    'first_name': 'Test',
                    'last_name': 'Parent'
                }
            )
            
            if created:
                self.stdout.write('Created test user')
            

            parent_profile, created = ParentProfile.objects.get_or_create(
                user=user,
                defaults={'phone': '1234567890'}
            )
            
            if created:
                self.stdout.write('Created parent profile')
            

            admin_user, created = User.objects.get_or_create(
                username='test_admin',
                defaults={
                    'email': 'admin@test.com',
                    'first_name': 'Test',
                    'last_name': 'Admin'
                }
            )
            
            from accounts.models import AcademyAdminProfile
            admin_profile, created = AcademyAdminProfile.objects.get_or_create(
                user=admin_user
            )
            

            academy, created = Academy.objects.get_or_create(
                name='Test Academy',
                defaults={
                    'description': 'Test Academy for invoice testing',
                    'city': 'Test City',
                    'email': 'academy@test.com',
                    'owner': admin_profile
                }
            )
            
            if created:
                self.stdout.write('Created test academy')
            
  
            program, created = Program.objects.get_or_create(
                title='Test Program',
                academy=academy,
                defaults={
                    'short_description': 'Test program for invoice testing',
                    'sport_type': 'football'
                }
            )
            
            if created:
                self.stdout.write('Created test program')
            

            child, created = Child.objects.get_or_create(
                parent=parent_profile,
                first_name='Test',
                defaults={
                    'last_name': 'Child',
                    'gender': 'M',
                    'primary_sport': 'football',
                    'skill_level': 'beginner'
                }
            )
            
            if created:
                self.stdout.write('Created test child')
            
 
            subscription, created = PlayerSubscription.objects.get_or_create(
                title='Test Subscription',
                academy=academy,
                defaults={
                    'price': Decimal('100.00'),
                    'billing_type': '3m',
                    'description': 'Test subscription for invoice testing'
                }
            )
            
            if created:
                self.stdout.write('Created test subscription')
            

            enrollment, created = PlayerEnrollment.objects.get_or_create(
                subscription=subscription,
                child=child,
                parent=user,
                start_date=date.today(),
                defaults={
                    'status': 'active',
                    'payment_method': 'card',
                    'end_date': date.today() + timedelta(days=90),
                    'amount_paid': Decimal('100.00'),
                    'payment_date': None
                }
            )
            
            if created:
                self.stdout.write('Created test enrollment')
            
 
            transaction, created = PaymentTransaction.objects.get_or_create(
                enrollment=enrollment,
                transaction_type='initial',
                defaults={
                    'status': 'completed',
                    'amount': Decimal('100.00'),
                    'currency': 'SAR',
                    'notes': 'Test payment transaction'
                }
            )
            
            if created:
                self.stdout.write('Created test transaction')
            

            self.stdout.write('Sending test invoice email...')
            success = send_payment_invoice_email(transaction, enrollment, user)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Test invoice email sent successfully!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Failed to send test invoice email')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during test: {str(e)}')
            )
