# coding: utf-8

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.views.generic.list_detail import object_list, object_detail

from csvimporter.models import CSV
from csvimporter.forms import CSVUploadForm, CSVImportForm


# TODO: Make this view class based
def prepare_view(request, kwargs):
    if not kwargs.get("model"):
        raise ValueError("You haven't specified the model")
    else:
        kwargs["app_label"] = kwargs["model"]._meta.app_label
        kwargs["model_name"] = kwargs["model"]._meta.module_name
        kwargs["redirect_url"] = reverse(
                "admin:%s_%s_changelist" % (kwargs["app_label"],
                                            kwargs["model_name"])
                )
        kwargs["extra_context"] = {
            "app_label": kwargs["app_label"],
            "model_name": kwargs["model_name"],
            "redirect_url": kwargs["redirect_url"],
        }
    return kwargs


@staff_member_required
def csv_list(request, **kwargs):
    kwargs = prepare_view(request, kwargs)
    if not kwargs.get("template_name"):
        kwargs["template_name"] = 'csvimporter/csv_list.html'
    return object_list(request,
        queryset=CSV.objects.all(),
        template_name=kwargs["template_name"],
        template_object_name='csv',
        extra_context=kwargs["extra_context"],
    )


@staff_member_required
def csv_upload(request, **kwargs):
    if not kwargs.get("template_name"):
        kwargs["template_name"] = 'csvimporter/csv_upload.html'
    if not kwargs.get("form_class"):
        kwargs["form_class"] = CSVUploadForm
    kwargs = prepare_view(request, kwargs)
    if request.method == 'POST':
        form = kwargs["form_class"](kwargs["model"],
                                    request.POST, request.FILES)
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(
                        reverse('csv_import', args=[instance.id]))
    else:
        form = kwargs["form_class"](kwargs["model"])
    kwargs["extra_context"].update({"form": form})
    return render_to_response(kwargs["template_name"],
        kwargs["extra_context"],
        context_instance=RequestContext(request)
    )


@staff_member_required
def csv_import(request, object_id, **kwargs):
    if not kwargs.get("template_name"):
        kwargs["template_name"] = 'csvimporter/csv_import.html'
    if not kwargs.get("form_class"):
        kwargs["form_class"] = CSVImportForm
    kwargs = prepare_view(request, kwargs)
    instance = get_object_or_404(CSV, pk=object_id)
    if request.method == 'POST':
        form = kwargs["form_class"](instance, request.POST)
        if form.is_valid():
            form.save(request)
            request.user.message_set.create(message=_('CSV imported.'))
            kwargs["redirect_url"] = reverse('csv_result', args=[instance.id])
            return HttpResponseRedirect(kwargs["redirect_url"])
    else:
        messages.info(request, _('Uploaded CSV. Please associate fields below.'))
        form = CSVImportForm(instance)
    kwargs["extra_context"].update({"form": form})
    return object_detail(request,
        queryset=CSV.objects.all(),
        object_id=object_id,
        template_name=kwargs["template_name"],
        template_object_name='csv',
        extra_context=kwargs["extra_context"],
    )


@staff_member_required
def csv_result(request, object_id, **kwargs):
    if not kwargs.get("template_name"):
        kwargs["template_name"] = 'csvimporter/csv_result.html'
    kwargs = prepare_view(request, kwargs)
    
    instance = get_object_or_404(CSV, pk=object_id)
    if instance.result_id_list:
        id_list = instance.result_id_list.split(',')
        object_list = kwargs['model'].objects.filter(id__in=instance.result_id_list.split(','))
        kwargs["extra_context"].update({"object_list": object_list})
    
    return render_to_response(kwargs["template_name"],
        kwargs["extra_context"],
        context_instance=RequestContext(request)
    )