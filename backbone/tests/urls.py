from django.conf.urls import patterns, url, include
from django.contrib import admin

import backbone


admin.autodiscover()
backbone.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^backbone/', include(backbone.site.urls)),
    url(r'^$', 'backbone.tests.views.homepage', name='tests-homepage'),
)
