import backbone
from backbone.views import BackboneAPIView
from backbone.tests.forms import BrandForm
from backbone.tests.models import Product, Brand


class ProductBackboneView(BackboneAPIView):
    model = Product
    display_fields = ('creation_date', 'name', 'brand', 'categories',
        'price', 'order', 'foo',)
    fields = ('name', 'brand', 'categories', 'price', 'order',)
    ordering = ('order', 'id')

    def queryset(self, request):
        qs = super(ProductBackboneView, self).queryset(request)
        return qs.filter(is_hidden=False)

backbone.site.register(ProductBackboneView)


class BrandBackboneView(BackboneAPIView):
    model = Brand
    form = BrandForm
    list_display = ('creation_date', 'name',)
    fields = ('name',)
    ordering = ('order', 'id')

    def has_delete_permission(self, request, id):
        return False

backbone.site.register(BrandBackboneView)
