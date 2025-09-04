from django import forms
from .models import Child, Enrollment
from academies.models import Program

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['child', 'program']

    def __init__(self, *args, **kwargs):
        parent = kwargs.pop('parent', None)
        super().__init__(*args, **kwargs)

        if parent:
            self.fields['child'].queryset = Child.objects.filter(parent=parent)
            self.fields['program'].queryset = Program.objects.filter(academy__isnull=False)

        self.fields['child'].label = "Select Child"
        self.fields['child'].help_text = "Choose which child to enroll"
        self.fields['program'].label = "Select Program"
        self.fields['program'].help_text = "Choose the academy program to enroll in"

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-select'})


class ParentPaymentForm(forms.Form):
    """Form for parent-player payment processing"""


    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('transfer', 'Bank Transfer'),
        ('cash', 'Cash Payment'),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect,
        initial='card'
    )


    cardholder_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cardholder Name'
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

 
    bank_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bank Name'
        })
    )

    account_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Account Number'
        })
    )

 
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any additional notes or instructions...'
        })
    )

 
    terms_agreement = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')

     
        if payment_method == 'card':
            if not cleaned_data.get('cardholder_name'):
                raise forms.ValidationError("Cardholder name is required for card payments")
            if not cleaned_data.get('card_number'):
                raise forms.ValidationError("Card number is required for card payments")
            if not cleaned_data.get('expiry_date'):
                raise forms.ValidationError("Expiry date is required for card payments")
            if not cleaned_data.get('cvv'):
                raise forms.ValidationError("CVV is required for card payments")

   
        elif payment_method == 'transfer':
            if not cleaned_data.get('bank_name'):
                raise forms.ValidationError("Bank name is required for bank transfers")
            if not cleaned_data.get('account_number'):
                raise forms.ValidationError("Account number is required for bank transfers")

        return cleaned_data
