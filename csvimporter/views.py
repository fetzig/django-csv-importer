import datetime, csv

from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.files.base import ContentFile
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.generic.list_detail import object_list, object_detail
from django.contrib import messages

from csvimporter.models import CSV
from csvimporter.forms import CSVForm, CSVAssociateForm

CSVIMPORTER_REDIRECT_URL = getattr(
    settings, "CSVIMPORTER_REDIRECT_URL", "csv-list")
CSVIMPORTER_DEFAULT_APP = getattr(settings, "CSVIMPORTER_DEFAULT_APP", None)

@staff_member_required
def csv_list(request, **kwargs):
    return object_list(request, queryset=CSV.objects.all(), template_name='csvimporter/csv_list.html', template_object_name='csv')

@staff_member_required
def associate(
    request, object_id, redirect_url=CSVIMPORTER_REDIRECT_URL, **kwargs
    ):
    instance = get_object_or_404(CSV, pk=object_id)
    if request.method == 'POST':
        form = CSVAssociateForm(instance, request.POST)
        if form.is_valid():
            form.save(request)
            request.user.message_set.create(message='CSV imported.')
            return HttpResponseRedirect(reverse(redirect_url))
    else:
        messages.info(request, 'Uploaded CSV. Please associate fields below.')
        form = CSVAssociateForm(instance)
    return object_detail(request,
        queryset=CSV.objects.all(),
        object_id=object_id,
        template_name='csvimporter/csv_detail.html',
        template_object_name='csv',
        extra_context={
            'form':form,
        })
    
@staff_member_required
def new(request, app=CSVIMPORTER_DEFAULT_APP, **kwargs):
    if request.method == 'POST':
        form = CSVForm(app, request.POST, request.FILES)
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(reverse('associate-csv',args=[instance.id]))
    else:
        form = CSVForm(app)
    return render_to_response('csvimporter/new.html',
        {'form':form}, context_instance=RequestContext(request))