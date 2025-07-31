from django import forms
from users.models import CustomUser
from django.contrib.auth.models import Group

class CustomUserAdminForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Assign groups (roles) to the user"
    )
    class Meta:
        model = CustomUser
        fields = '__all__'