# Parent Payment Invoice Email System

## Overview
This system automatically sends invoice emails to parents when they complete payments for their children's academy enrollments.

## How It Works

### 1. Payment Processing
When a parent completes a payment through the `/parents/payments/` page:
- The `process_payment` view in `parents/views.py` handles the payment
- A `PaymentTransaction` record is created
- The `PlayerEnrollment` status is updated to 'active'

### 2. Invoice Email Sending
After successful payment processing:
- The `send_payment_invoice_email()` function is called
- An HTML and text email is generated using Django templates
- The email is sent to the parent's email address

### 3. Email Templates
- **HTML Template**: `parents/templates/parents/emails/payment_invoice.html`
- **Text Template**: `parents/templates/parents/emails/payment_invoice.txt`

Both templates include:
- Payment confirmation
- Invoice details (transaction ID, date, method)
- Enrollment information (child, academy, program)
- Payment summary
- Next steps for the parent

## Files Modified/Created

### New Files:
- `parents/utils.py` - Email sending utility function
- `parents/templates/parents/emails/payment_invoice.html` - HTML email template
- `parents/templates/parents/emails/payment_invoice.txt` - Text email template
- `parents/management/commands/test_invoice_email.py` - Test command
- `parents/README_INVOICE_EMAIL.md` - This documentation

### Modified Files:
- `parents/views.py` - Added email sending to payment processing

## Testing

### Test the Email System:
```bash
python manage.py test_invoice_email --email="your-email@example.com"
```

This command will:
1. Create test data (user, academy, program, enrollment, transaction)
2. Send a test invoice email
3. Report success/failure

### Manual Testing:
1. Go to `http://127.0.0.1:8000/parents/payments/`
2. Complete a payment with a valid email address
3. Check the parent's email for the invoice

## Email Configuration

The system uses the email settings from `settings.py`:
- **SMTP Host**: smtp.gmail.com
- **Port**: 587
- **TLS**: Enabled
- **From Email**: xsketty@gmail.com

## Error Handling

- If email sending fails, the payment still completes successfully
- A message is shown to the user indicating email status
- Errors are logged for debugging
- The system gracefully handles missing or invalid data

## Customization

### Email Content:
Edit the templates in `parents/templates/parents/emails/` to customize:
- Email styling and layout
- Information included in the invoice
- Academy branding

### Email Settings:
Modify `EMAIL_*` settings in `settings.py` to use different email providers.

## Security Notes

- Email addresses are validated before sending
- Only authenticated parents can trigger payment processing
- Payment amounts are verified against subscription plans
- Transaction IDs are used for tracking and reference

