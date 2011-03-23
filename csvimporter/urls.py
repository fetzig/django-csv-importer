"""
this is an example:

urlpatterns += patterns('csvimporter.views',
    url(r'^csvimporter/list/$', 'csv_list', kwargs={"model": Restaurant}, name='csv_list'),
    url(r'^csvimporter/upload/$', 'csv_upload', kwargs={"model": Restaurant}, name='csv_upload'),
    url(r'^csvimporter/import/(?P<object_id>\d+)/$', 'csv_import', kwargs={"model": Restaurant}, name='csv_import'),
    url(r'^csvimporter/result/(?P<object_id>\d+)/$', 'csv_result', kwargs={"model": Restaurant}, name='csv_result'),
)

"""

