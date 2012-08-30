from django import forms
from django.utils.translation import ugettext_lazy as _

from backbone.tests.models import Brand


class BrandForm(forms.ModelForm):

    class Meta:
        model = Brand
        fields = ('name',)

    def clean_name(self):
        name = self.cleaned_data['name']
        if name:
            if name[0] != name[0].upper():
                # A silly rule just for the purpose of testing.
                raise forms.ValidationError(_('Brand name must start with a capital letter.'))
        return name