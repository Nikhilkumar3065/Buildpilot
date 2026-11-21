from django import forms
from .models import Client, Problem


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email']


class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['client', 'description']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe the client problem in simple words...'
            })
        }
