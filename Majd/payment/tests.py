from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail
from .models import PlanType, Subscription
from django.utils import timezone
from datetime import timedelta


class SubscriptionNotificationTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create a test plan type
        self.plan_type = PlanType.objects.create(
            name='Test Plan',
            monthly_price=100.00,
            features=['Feature 1', 'Feature 2']
        )
        
        # Create a test subscription
        self.subscription = Subscription.objects.create(
            academy_name='Test Academy',
            plan_type=self.plan_type,
            price=100.00,
            duration_days=30,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
            payment_method=Subscription.PaymentMethod.CARD,
            contact_email='test@academy.com',
            billing_address='123 Test Street, Test City',
            status=Subscription.Status.PENDING
        )

    def test_subscription_creation(self):
        """Test that subscription can be created"""
        self.assertEqual(self.subscription.academy_name, 'Test Academy')
        self.assertEqual(self.subscription.plan_type, self.plan_type)
        self.assertEqual(self.subscription.status, Subscription.Status.PENDING)

    def test_status_change_notification(self):
        """Test that status change triggers notification"""
        # Clear mail outbox
        mail.outbox = []
        
        # Change status to trigger notification
        self.subscription.status = Subscription.Status.SUCCESSFUL
        self.subscription.save()
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], 'test@academy.com')
        self.assertIn('Subscription Successful', mail.outbox[0].subject)

    def test_invoice_email(self):
        """Test that invoice email can be sent"""
        # Clear mail outbox
        mail.outbox = []
        
        # Send invoice
        self.subscription.send_invoice()
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], 'test@academy.com')
        self.assertIn('Invoice for', mail.outbox[0].subject)

    def test_subscription_str_representation(self):
        """Test subscription string representation"""
        expected = f"Test Academy - Test Plan (pending)"
        self.assertEqual(str(self.subscription), expected)


class CheckoutViewTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.plan_type = PlanType.objects.create(
            name='Test Plan',
            monthly_price=150.00,
            features=['Feature 1', 'Feature 2']
        )

    def test_checkout_form_submission(self):
        """Test checkout form submission creates subscription"""
        form_data = {
            'academy_name': 'New Test Academy',
            'contact_email': 'new@academy.com',
            'contact_phone': '+966501234567',
            'city': 'Riyadh',
            'address': '456 New Street, Riyadh',
            'payment_method': 'card',
            'terms_agreement': True,
            'marketing_emails': False
        }
        
        response = self.client.post(
            reverse('payment:checkout', args=[self.plan_type.id]),
            data=form_data
        )
        
        # Should redirect to success page
        self.assertEqual(response.status_code, 302)
        
        # Check that subscription was created
        subscription = Subscription.objects.filter(
            academy_name='New Test Academy',
            contact_email='new@academy.com'
        ).first()
        
        self.assertIsNotNone(subscription)
        self.assertEqual(subscription.plan_type, self.plan_type)
        self.assertEqual(subscription.price, 150.00)


class EmailTemplateTest(TestCase):
    def setUp(self):
        """Set up test data for template testing"""
        self.plan_type = PlanType.objects.create(
            name='Premium Plan',
            monthly_price=200.00,
            features=['Advanced Features', 'Priority Support', 'Custom Branding']
        )
        
        self.subscription = Subscription.objects.create(
            academy_name='Premium Academy',
            plan_type=self.plan_type,
            price=200.00,
            duration_days=30,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
            payment_method=Subscription.PaymentMethod.CARD,
            contact_email='premium@academy.com',
            billing_address='789 Premium Street, Premium City',
            status=Subscription.Status.SUCCESSFUL,
            transaction_id='TXN123456',
            payment_date=timezone.now()
        )

    def test_subscription_status_template_rendering(self):
        """Test that subscription status template renders correctly"""
        from django.template.loader import render_to_string
        
        context = {
            'subscription': self.subscription,
            'academy': {'name': self.subscription.academy_name},
            'plan_type': self.subscription.plan_type,
            'status_display': self.subscription.get_status_display(),
            'payment_method_display': self.subscription.get_payment_method_display(),
        }
        
        html_content = render_to_string('payment/emails/subscription_status.html', context)
        text_content = render_to_string('payment/emails/subscription_status.txt', context)
        
        # Check that content is rendered
        self.assertIn('Premium Academy', html_content)
        self.assertIn('Premium Plan', html_content)
        self.assertIn('Successful', html_content)
        self.assertIn('SAR 200.00', html_content)
        
        # Check text version
        self.assertIn('Premium Academy', text_content)
        self.assertIn('Premium Plan', text_content)

    def test_invoice_template_rendering(self):
        """Test that invoice template renders correctly"""
        from django.template.loader import render_to_string
        
        context = {
            'subscription': self.subscription,
            'academy': {'name': self.subscription.academy_name},
            'plan_type': self.subscription.plan_type,
            'invoice_date': timezone.now().date(),
        }
        
        html_content = render_to_string('payment/emails/invoice.html', context)
        text_content = render_to_string('payment/emails/invoice.txt', context)
        
        # Check that content is rendered
        self.assertIn('INVOICE', html_content)
        self.assertIn('Premium Academy', html_content)
        self.assertIn('Premium Plan', html_content)
        self.assertIn('SAR 200.00', html_content)
        
        # Check text version
        self.assertIn('INVOICE', text_content)
        self.assertIn('Premium Academy', text_content)
        self.assertIn('Premium Plan', text_content)
