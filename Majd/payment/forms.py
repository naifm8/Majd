from django import forms

class CheckoutForm(forms.Form):
    # Academy Information
    academy_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter academy name'
        })
    )
    contact_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'contact@academy.com'
        })
    )
    contact_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+966 50 123 4567'
        })
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Riyadh'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter full address'
        })
    )
    
    # Payment Method
    payment_method = forms.ChoiceField(
        choices=[
            ('card', 'Credit/Debit Card'),
            ('transfer', 'Bank Transfer')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    # Card Details (only shown when card is selected)
    cardholder_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name on card'
        })
    )
    card_number = forms.CharField(
        max_length=19,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456'
        })
    )
    expiry_date = forms.CharField(
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/YY'
        })
    )
    cvv = forms.CharField(
        max_length=4,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123'
        })
    )
    
    # Agreements
    terms_agreement = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    marketing_emails = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        
        if payment_method == 'card':
            if not cleaned_data.get('cardholder_name'):
                self.add_error('cardholder_name', 'Cardholder name is required for card payments')
            if not cleaned_data.get('card_number'):
                self.add_error('card_number', 'Card number is required for card payments')
            if not cleaned_data.get('expiry_date'):
                self.add_error('expiry_date', 'Expiry date is required for card payments')
            if not cleaned_data.get('cvv'):
                self.add_error('cvv', 'CVV is required for card payments')
        
        return cleaned_data
