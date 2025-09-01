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
            # Filter children to only show the parent's children
            self.fields['child'].queryset = Child.objects.filter(parent=parent)
            
            # Filter programs to only show active programs from academies
            self.fields['program'].queryset = Program.objects.filter(academy__isnull=False)
        
        # Add custom labels and help text
        self.fields['child'].label = "Select Child"
        self.fields['child'].help_text = "Choose which child to enroll"
        
        self.fields['program'].label = "Select Program"
        self.fields['program'].help_text = "Choose the academy program to enroll in"
        
        # Add Bootstrap classes
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-select'})
