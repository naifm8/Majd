from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime


def send_payment_invoice_email(transaction, enrollment, parent_user):
    """
    Send payment invoice email to parent after successful payment
    """
    try:
        # Calculate VAT and base amount
        total_amount = float(transaction.amount)
        base_amount = total_amount / 1.15  # Remove VAT to get base amount
        vat_amount = total_amount - base_amount
        
        # Prepare email context
        context = {
            'parent_name': f"{parent_user.first_name} {parent_user.last_name}".strip() or parent_user.username,
            'child_name': f"{enrollment.child.first_name} {enrollment.child.last_name}".strip(),
            'academy_name': enrollment.subscription.academy.name,
            'program_title': enrollment.subscription.program.title if enrollment.subscription.program else enrollment.subscription.title,
            'sport_type': enrollment.subscription.program.sport_type.title() if enrollment.subscription.program else 'General',
            'amount': total_amount,
            'base_amount': round(base_amount, 2),
            'vat_amount': round(vat_amount, 2),
            'currency': transaction.currency,
            'payment_method': enrollment.payment_method.title(),
            'payment_date': transaction.processed_at.strftime('%B %d, %Y at %I:%M %p') if transaction.processed_at else 'N/A',
            'transaction_id': transaction.id,
            'start_date': enrollment.start_date.strftime('%B %d, %Y'),
            'end_date': enrollment.end_date.strftime('%B %d, %Y'),
            'academy_email': enrollment.subscription.academy.email,
            'current_year': datetime.now().year,
        }
        
        # Render email templates
        html_content = render_to_string('parents/emails/payment_invoice.html', context)
        text_content = render_to_string('parents/emails/payment_invoice.txt', context)
        
        # Create email
        subject = f"Payment Invoice - {context['academy_name']} - Transaction #{context['transaction_id']}"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[parent_user.email]
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        return True
        
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending invoice email: {str(e)}")
        return False
