# coding: utf-8

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils.translation import ugettext as _


class CSV(models.Model):
    
    upload_to = getattr(settings, 'CSVIMPORTER_UPLOAD_TO', 'csvimporter')
    
    content_type = models.ForeignKey(ContentType)
    csv_file     = models.FileField(_(u"CSV File"), upload_to=upload_to)
    created      = models.DateTimeField(auto_now_add=True)
    
    result_id_list = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ["-id"]
    
    @property
    def filename(self):
        """
        This is a helper method, so that you can display the name of the file a user uploaded, without
        the name of the directory the file was uploaded to.
        """
        return self.csv_file.name.replace('%s/' % self.upload_to, '')