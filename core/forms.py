from django import forms
from .models import (
    Client,
    Problem,
    RequirementVersion,
    TechnicalPlan,
    BugReport
)


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


class RequirementForm(forms.ModelForm):
    class Meta:
        model = RequirementVersion
        fields = [
            'problem_statement',
            'users',
            'must_do',
            'must_not_do',
            'success_criteria',
            'open_questions'
        ]

        widgets = {
            'problem_statement': forms.Textarea(attrs={'rows': 4}),
            'users': forms.Textarea(attrs={'rows': 3}),
            'must_do': forms.Textarea(attrs={'rows': 4}),
            'must_not_do': forms.Textarea(attrs={'rows': 4}),
            'success_criteria': forms.Textarea(attrs={'rows': 4}),
            'open_questions': forms.Textarea(attrs={'rows': 3}),
        }
class TechnicalPlanForm(forms.ModelForm):

    class Meta:
        model = TechnicalPlan
        fields = ['content']

        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 20,
                'placeholder': 'Review and edit the technical plan...'
            })
        }

class BugReportForm(forms.ModelForm):

    class Meta:
        model = BugReport

        fields = [
            'title',
            'steps_to_reproduce',
            'expected_behavior',
            'actual_behavior',
        ]

        labels = {
            'title': 'Bug Title',
            'steps_to_reproduce': 'Steps to Reproduce',
            'expected_behavior': 'Expected Behavior',
            'actual_behavior': 'Actual Behavior',
        }

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a short bug title',
                'maxlength': 200,
            }),

            'steps_to_reproduce': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the steps to reproduce the bug...',
            }),

            'expected_behavior': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what should happen...',
            }),

            'actual_behavior': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what actually happens...',
            }),
        }