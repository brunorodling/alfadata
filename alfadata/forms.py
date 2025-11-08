from django import forms

class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(
        label='Arquivo Excel (.xlsx ou .xls)',
        widget=forms.ClearableFileInput(attrs={'accept': '.xls,.xlsx'})
    )
