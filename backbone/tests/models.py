from django.db import models
from django.utils.translation import ugettext_lazy as _


class Brand(models.Model):
    name = models.CharField(_('name'), max_length=255)

    class Meta:
        ordering = ('id',)


class Category(models.Model):
    name = models.CharField(_('name'), max_length=255)

    class Meta:
        ordering = ('id',)


class Product(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, null=True, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    is_hidden = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    order = models.PositiveSmallIntegerField(default=0)
    sku = models.CharField(max_length=255)
    sale_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('id',)

    @property
    def is_priced_under_10(self):
        return self.price < 10

    def get_first_category_id(self):
        if self.categories.count():
            return self.categories.all()[0].id
        else:
            return None


class ExtendedProduct(Product):
    description = models.CharField(max_length=255)


class DisplayFieldsProduct(Product):
    description = models.CharField(max_length=255)
