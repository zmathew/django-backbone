from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib import admin

import backbone

admin.autodiscover()
backbone.autodiscover()

from backbone.tests.views import homepage

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^backbone/', include(backbone.site.urls)),
    url(r'^$', homepage, name='tests-homepage'),
]
