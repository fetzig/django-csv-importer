# coding: utf-8

import re
from copy import copy

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db import IntegrityError
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.utils.encoding import force_unicode

from csvimporter.models import CSV
from csvimporter.utils import create_csv_reader


class CSVUploadForm(forms.ModelForm):
    """
    uploads csv and check if its "valid".
    """
    def __init__(self, model=None, *args, **kwargs):
        self.model = model
        super(CSVUploadForm, self).__init__(*args, **kwargs)
        content_types = ContentType.objects.all()
        self.fields['content_type'] = forms.ModelChoiceField(queryset=content_types)
        
        if self.model:
            self.fields['content_type'].initial = (
                content_types.get(model=self.model._meta.module_name))
            self.fields['content_type'].widget = forms.widgets.HiddenInput()
    
    def clean_csv_file(self):
        if not 'csv_file' in self.cleaned_data:
            raise forms.ValidationError("No File selected.")
        # check file extension (.csv)
        if not self.cleaned_data['csv_file'].name.endswith(".csv"):
            raise forms.ValidationError("Wrong File extension.")
        # check if file can be parsed by pythons csv.DictReader()
        try:
            reader = create_csv_reader(self.cleaned_data['csv_file'].file)
        except:
            raise forms.ValidationError("Can't process file. Are you sure this is a csv file?")
        # check if format of csv is valid
        for field_name in reader.fieldnames:
            # check if we know all field_names
            # if not the csv is invalid => this raises an KeyError
            try:
                mapped_field_name = self.model.csvimporter['csv_associate'](field_name)
            except KeyError, e:
                raise forms.ValidationError('CSV is invalid. Fieldname "%s" is unknown.' % field_name)
        return self.cleaned_data['csv_file']
    
    class Meta:
        model = CSV
        exclude = ('result_id_list',)


class CSVImportForm(forms.Form):
    """
    imports the data of a csv into the db.
    """
    def __init__(self, instance, *args, **kwargs):
        self.instance = instance
        self.reader = create_csv_reader(instance.csv_file.file)
        self.klass = self.instance.content_type.model_class()
        # pylint: disable-msg=W0212
        choices = ([(None, '---- (None)')] +
                   [(f.name, f.name) for f in self.klass._meta.fields])
        super(CSVImportForm, self).__init__(*args, **kwargs)
        for field_name in self.reader.fieldnames:
            self.fields[field_name] = forms.ChoiceField(choices=choices, required=False)
            mapped_field_name = self.klass.csvimporter['csv_associate'](field_name)
            if mapped_field_name in [f.name for f in self.klass._meta.fields]:
                self.fields[field_name].initial = mapped_field_name
            else:
                _choices = copy(choices)
                _choices.append((mapped_field_name, mapped_field_name))
                self.fields[field_name] = forms.ChoiceField(choices=_choices, required=False)
                self.fields[field_name].initial = mapped_field_name
    
    def clean(self):
        validators = self.klass.csvimporter.get('csv_validate', lambda d, i: d)
        
        line = 1
        errors = []
        
        for row in self.reader.rows:
            data = {}
            for field_name in self.reader.fieldnames:
                data[self.cleaned_data[field_name]] = row[field_name]
            result = validators(data, line)
            errors.extend(result)
            line += 1
        if len(errors) > 0:
            raise forms.ValidationError(errors)
        
        return super(CSVImportForm, self).clean()
        
    def save(self, request):
        # these are out here because we only need
        # to retreive them from settings the once.
        transforms = self.klass.csvimporter.get('csv_transform', lambda r, d: d)
        dups = 0
        ok = 0
        result_id_list = None
        for row in self.reader.rows:
            data = {}
            for field_name in self.reader.fieldnames:
                data[self.cleaned_data[field_name]] = row[field_name]
            data = transforms(request, data)
            new_obj = self.klass()
            for key in data.keys():
                try:
                    field = new_obj._meta.get_field(key)
                except FieldDoesNotExist:
                    continue
                # Cleaning
                if type(data[key]) in (str, unicode):
                    data[key] = re.sub(r"^ +$", "", force_unicode(data[key]))
                if type(field) in [models.IntegerField, models.FloatField]:
                    data[key] = data[key].replace(",", "")
                    if not data[key]:
                        data[key] = None
                setattr(new_obj, key, data[key])
            try:
                new_obj.save()
                ok += 1
                if result_id_list == None:
                    result_id_list = str(new_obj.pk)
                else:
                    result_id_list += "," + str(new_obj.pk)
            except IntegrityError, e:
                if 'unique' in str(e):
                    dups += 1
                else:
                    raise
        
        if ok:
            messages.info(request, _("Successfully imported %s records.") % ok)
        if dups:
            messages.warning(request, _("%s records skipped because of duplication.") % dups)
        
        self.instance.result_id_list = result_id_list
        self.instance.save()
