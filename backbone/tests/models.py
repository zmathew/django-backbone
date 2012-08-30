from django.db import models
from django.utils.translation import ugettext_lazy as _


class Brand(models.Model):
    name = models.CharField(_('name'), max_length=255)


class Category(models.Model):
    name = models.CharField(_('name'), max_length=255)


class Product(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, null=True, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    is_hidden = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ('id',)

    @property
    def foo(self):
        return 'foo'
