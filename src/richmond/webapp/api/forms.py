from django import forms
from richmond.webapp.api.models import SentSMS, URLCallback

class SentSMSForm(forms.ModelForm):
    class Meta:
        model = SentSMS
    user = forms.IntegerField(required=False)

class URLCallbackForm(forms.ModelForm):
    class Meta:
        model = URLCallback

class ReceivedSMSForm(forms.Form):
    user_id = forms.IntegerField(required=False)
    api_id = forms.CharField()
    moMsgId = forms.CharField()
    # would like to automatically validate from but the keyword is special
    # in python, leaving it 'required=False' for now
    _from = forms.CharField(max_length=32, required=False)
    to = forms.CharField()
    timestamp = forms.DateTimeField()
    charset = forms.CharField(required=False)
    udh = forms.CharField(required=False)
    text = forms.CharField()


class SMSReceiptForm(forms.Form):
    user_id = forms.IntegerField(required=False)
    cliMsgId = forms.IntegerField()
    apiMsgId = forms.CharField(max_length=32)
    status = forms.IntegerField()
    timestamp = forms.IntegerField()
    to = forms.CharField(max_length=32)
    # would like to automatically validate from but the keyword is special
    # in python, leaving it 'required=False' for now
    _from = forms.CharField(max_length=32, required=False)
    charge = forms.FloatField()

