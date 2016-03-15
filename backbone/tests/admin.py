from __future__ import unicode_literals

from django.contrib import admin

from backbone.tests.models import Product, Brand


admin.site.register(Product)
admin.site.register(Brand)
