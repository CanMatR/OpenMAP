from django import forms
from django.core.exceptions import ValidationError

from map_base.models import Campaign, MapInput

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = [ 'name',
                    'for_map',
                    'with_ml',
                    'max_experiments',
                    ]

class ExperimentForm(forms.Form):
    label = forms.CharField()

class ExpInputForm(forms.Form):
    campaign_name = forms.CharField(widget=forms.HiddenInput())
    input_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'readonly':'readonly'}))
    input_value = forms.FloatField()

    def clean(self):
        cleaned_data = super().clean()
        campaign_name = cleaned_data.get("campaign_name")
        input_name = cleaned_data.get("input_name")
        input_value = cleaned_data.get("input_value")

        if campaign_name and input_name and input_value:
            try:
                campaign = Campaign.objects.get(name=campaign_name)
                map_input = MapInput.objects.get(for_map=campaign.for_map, name=input_name)
            except Campaign.DoesNotExist:
                raise ValidationError( "Form not associated with a valid campaign.", code='invalid' )
            except MapInput.DoesNotExist:
                raise ValidationError( "Invalid input name.", code='invalid' )

            if input_value < map_input.min_val or input_value > map_input.max_val:
                raise ValidationError( 'Value for %(name)s must lie between min (%(minval)f) and max (%(maxval)f).', code='invalid',
                                        params={ 'name': input_name, 'minval': map_input.min_val, 'maxval': map_input.max_val })


class BaseInputFormSet(forms.BaseFormSet):
    def clean(self):
        # require individual forms to be valid before applying group validation
        if any(self.errors):
            return

        names =  []
        for form in self.forms:
            input_name = form.cleaned_data.get('input_name')
            if input_name in names:
                raise ValidationError('Do not specify the same input variable twice.', code='invalid')
            names.append(input_name)
