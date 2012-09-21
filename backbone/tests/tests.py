from decimal import Decimal

from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import simplejson
from django.utils.translation import ugettext as _

from backbone.tests.models import Product, Brand, Category
from backbone.tests.backbone_api import ProductBackboneView


class TestHelper(TestCase):

    def parseJsonResponse(self, response, status_code=200):
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = simplejson.loads(response.content)
        return data

    def create_product(self, **kwargs):
        defaults = {
            'name': 'Test Product',
            'price': '12.32'
        }
        if 'brand' not in kwargs:
            defaults['brand'] = self.create_brand()
        defaults.update(kwargs)
        return Product.objects.create(**defaults)

    def create_brand(self, **kwargs):
        defaults = {
            'name': 'Test Brand',
        }
        defaults.update(kwargs)
        return Brand.objects.create(**defaults)

    def create_category(self, **kwargs):
        defaults = {
            'name': 'Test Category',
        }
        defaults.update(kwargs)
        return Category.objects.create(**defaults)


class CollectionTests(TestHelper):

    def test_collection_view_returns_all_products_in_order(self):
        p3 = self.create_product(order=3)
        p1 = self.create_product(order=1)
        p2 = self.create_product(order=2)

        url = reverse('backbone:tests_product')
        response = self.client.get(url)
        data = self.parseJsonResponse(response)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['id'], p1.id)
        self.assertEqual(data[0]['name'], p1.name)
        self.assertEqual(data[1]['id'], p2.id)
        self.assertEqual(data[1]['name'], p1.name)
        self.assertEqual(data[2]['id'], p3.id)
        self.assertEqual(data[2]['name'], p1.name)

    def test_collection_view_only_returns_fields_specified_in_display_fields(self):
        self.create_product()
        url = reverse('backbone:tests_product')
        response = self.client.get(url)
        data = self.parseJsonResponse(response)
        self.assertEqual(len(data), 1)
        fields = data[0].keys()

        self.assertEqual(set(['id'] + list(ProductBackboneView.display_fields)), set(fields))
        self.assertTrue('is_hidden' not in fields)

    def test_collection_view_foreign_key_is_returned_as_id(self):
        brand = self.create_brand()
        self.create_product(brand=brand)
        url = reverse('backbone:tests_product')
        response = self.client.get(url)
        data = self.parseJsonResponse(response)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['brand'], brand.id)

    def test_collection_view_m2m_field_is_returned_as_list_of_ids(self):
        cat1 = self.create_category()
        cat2 = self.create_category()
        p = self.create_product()
        p.categories = [cat1, cat2]
        url = reverse('backbone:tests_product')
        response = self.client.get(url)
        data = self.parseJsonResponse(response)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['categories'], [cat1.id, cat2.id])

    def test_collection_view_with_custom_queryset(self):
        p1 = self.create_product()
        self.create_product(is_hidden=True)  # this should not appear

        url = reverse('backbone:tests_product')
        response = self.client.get(url)
        data = self.parseJsonResponse(response)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], p1.id)

    def test_collection_view_put_request_returns_405(self):
        url = reverse('backbone:tests_product')
        response = self.client.put(url)
        self.assertEqual(response.status_code, 405)

    def test_collection_view_delete_request_returns_405(self):
        url = reverse('backbone:tests_product')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 405)


class DetailTests(TestHelper):

    def test_detail_view_returns_object_details(self):
        product = self.create_product()
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.get(url)
        data = self.parseJsonResponse(response)
        self.assertEqual(data['id'], product.id)
        self.assertEqual(data['name'], product.name)

    def test_detail_view_doesnt_return_unspecified_fields(self):
        product = self.create_product()
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.get(url)
        data = self.parseJsonResponse(response)
        fields = data.keys()
        self.assertTrue('is_hidden' not in fields)

    def test_detail_view_returns_404_for_invalid_id(self):
        url = reverse('backbone:tests_product_detail', args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_view_returns_404_for_object_not_in_custom_queryset(self):
        product = self.create_product(is_hidden=True)
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_view_post_request_returns_405(self):
        product = self.create_product()
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)


class AddTests(TestHelper):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test', email='t@t.com')
        self.client.login(username='test', password='test')
        add_product = Permission.objects.get_by_natural_key('add_product', 'tests', 'product')
        add_brand = Permission.objects.get_by_natural_key('add_brand', 'tests', 'brand')
        self.user.user_permissions = [add_product, add_brand]

    def test_post_request_on_product_collection_view_adds_product_to_db(self):
        brand = self.create_brand()
        cat1 = self.create_category()
        cat2 = self.create_category()
        data = simplejson.dumps({
            'name': 'Test',
            'brand': brand.id,
            'categories': [cat1.id, cat2.id],
            'price': 12.34,
            'order': 1
        })
        url = reverse('backbone:tests_product')
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        self.assertEqual(Product.objects.count(), 1)
        product = Product.objects.order_by('-id')[0]
        self.assertEqual(product.name, 'Test')
        self.assertEqual(product.brand, brand)
        self.assertEqual(product.categories.count(), 2)
        self.assertEqual(product.categories.all()[0], cat1)
        self.assertEqual(product.categories.all()[1], cat2)
        self.assertEqual(product.price, Decimal('12.34'))

        data = self.parseJsonResponse(response, status_code=201)
        self.assertEqual(data['id'], product.id)
        self.assertEqual(data['name'], product.name)
        self.assertEqual(data['brand'], product.brand.id)
        self.assertEqual(data['categories'], [cat1.id, cat2.id])
        self.assertEqual(data['price'], '12.34')

        self.assertEqual(response['Location'], 'http://testserver' \
            + reverse('backbone:tests_product_detail', args=[product.id])
        )

    def test_post_request_on_product_collection_view_with_invalid_json_returns_error(self):
        url = reverse('backbone:tests_product')
        response = self.client.post(url, '', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, _('Unable to parse JSON request body.'))

        response = self.client.post(url, 'Some invalid json', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, _('Unable to parse JSON request body.'))

    def test_post_request_on_product_collection_view_with_validation_errors_returns_error_list_as_json(self):
        data = simplejson.dumps({
            'name': '',
            'brand': '',
            'categories': [],
            'price': None,
            'order': '',
        })
        url = reverse('backbone:tests_product')
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(Product.objects.count(), 0)
        data = self.parseJsonResponse(response, status_code=400)
        self.assertEqual(len(data), 3)
        self.assertEqual(data['name'], [_('This field is required.')])
        self.assertEqual(data['price'], [_('This field is required.')])
        self.assertEqual(data['order'], [_('This field is required.')])

    def test_post_request_on_product_collection_view_ignores_fields_not_specified(self):
        brand = self.create_brand()
        cat1 = self.create_category()
        cat2 = self.create_category()
        data = simplejson.dumps({
            'name': 'Test',
            'brand': brand.id,
            'categories': [cat1.id, cat2.id],
            'price': 12.34,
            'order': 1,
            'is_hidden': True  # User should not be able to alter is_hidden
        })
        url = reverse('backbone:tests_product')
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Product.objects.count(), 1)
        product = Product.objects.order_by('-id')[0]
        self.assertEqual(product.is_hidden, False)

    def test_post_request_on_product_collection_view_when_user_not_logged_in_returns_403(self):
        self.client.logout()

        url = reverse('backbone:tests_product')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, _('You do not have permission to perform this action.'))
        self.assertEqual(Product.objects.count(), 0)

    def test_post_request_on_product_collection_view_when_user_doesnt_have_add_permission_returns_403(self):
        self.client.logout()
        self.user.user_permissions.clear()
        self.client.login(username='test', password='test')
        url = reverse('backbone:tests_product')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, _('You do not have permission to perform this action.'))

    def test_post_request_on_product_collection_view_violating_field_specific_permission_returns_403(self):
        brand = self.create_brand()
        cat1 = self.create_category()
        data = simplejson.dumps({
            'name': 'NOTALLOWED',
            'brand': brand.id,
            'categories': [cat1.id],
            'price': 12.34,
            'order': 1
        })
        url = reverse('backbone:tests_product')
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, _('You do not have permission to perform this action.'))

    def test_post_request_on_brand_collection_view_uses_custom_model_form(self):
        data = simplejson.dumps({
            'name': 'this should give an error',
        })
        url = reverse('backbone:tests_brand')
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(Product.objects.count(), 0)
        data = self.parseJsonResponse(response, status_code=400)
        self.assertEqual(len(data), 1)
        self.assertEqual(data['name'], [_('Brand name must start with a capital letter.')])


class UpdateTests(TestHelper):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test', email='t@t.com')
        self.client.login(username='test', password='test')
        update_product = Permission.objects.get_by_natural_key('change_product', 'tests', 'product')
        update_brand = Permission.objects.get_by_natural_key('change_brand', 'tests', 'brand')
        self.user.user_permissions = [update_product, update_brand]

    def test_put_request_on_product_detail_view_updates_product(self):
        product = self.create_product()

        brand = self.create_brand()
        cat1 = self.create_category()
        cat2 = self.create_category()
        data = simplejson.dumps({
            'name': 'Test',
            'brand': brand.id,
            'categories': [cat1.id, cat2.id],
            'price': 56.78,
            'order': 2
        })
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.put(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Product.objects.count(), 1)
        product = Product.objects.get(id=product.id)  # refresh from db
        self.assertEqual(product.name, 'Test')
        self.assertEqual(product.brand, brand)
        self.assertEqual(product.categories.count(), 2)
        self.assertEqual(product.categories.all()[0], cat1)
        self.assertEqual(product.categories.all()[1], cat2)
        self.assertEqual(product.price, Decimal('56.78'))

        data = self.parseJsonResponse(response, status_code=200)
        self.assertEqual(data['id'], product.id)
        self.assertEqual(data['name'], product.name)
        self.assertEqual(data['brand'], product.brand.id)
        self.assertEqual(data['categories'], [cat1.id, cat2.id])
        self.assertEqual(data['price'], '56.78')

    def test_put_request_on_product_detail_view_with_invalid_json_returns_error(self):
        product = self.create_product()

        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.put(url, '', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, _('Unable to parse JSON request body.'))

        response = self.client.put(url, 'Some invalid json', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, _('Unable to parse JSON request body.'))

    def test_put_request_on_product_detail_view_with_validation_errors_returns_error_list_as_json(self):
        product = self.create_product()
        data = simplejson.dumps({
            'name': '',
            'price': None,
            'order': '',
        })
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.put(url, data, content_type='application/json')
        self.assertEqual(Product.objects.count(), 1)
        data = self.parseJsonResponse(response, status_code=400)
        self.assertEqual(len(data), 3)
        self.assertEqual(data['name'], [_('This field is required.')])
        self.assertEqual(data['price'], [_('This field is required.')])
        self.assertEqual(data['order'], [_('This field is required.')])

    def test_put_request_on_product_detail_view_ignores_fields_not_specified(self):
        product = self.create_product()
        brand = self.create_brand()
        cat1 = self.create_category()
        cat2 = self.create_category()
        data = simplejson.dumps({
            'name': 'Test',
            'brand': brand.id,
            'categories': [cat1.id, cat2.id],
            'price': 12.34,
            'order': 1,
            'is_hidden': True  # User should not be able to alter is_hidden
        })
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.put(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        product = Product.objects.get(id=product.id)  # refresh from db
        self.assertEqual(product.is_hidden, False)

    def test_put_request_on_product_detail_view_when_user_not_logged_in_returns_403(self):
        product = self.create_product()
        self.client.logout()

        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, _('You do not have permission to perform this action.'))

    def test_put_request_on_product_detail_view_when_user_doesnt_have_update_permission_returns_403(self):
        product = self.create_product()
        self.client.logout()
        self.user.user_permissions.clear()
        self.client.login(username='test', password='test')

        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, _('You do not have permission to perform this action.'))

    def test_put_request_on_product_detail_view_violating_field_specific_permission_returns_403(self):
        product = self.create_product()
        brand = self.create_brand()
        cat1 = self.create_category()
        data = simplejson.dumps({
            'name': 'NOTALLOWED',
            'brand': brand.id,
            'categories': [cat1.id],
            'price': 12.34,
            'order': 2
        })
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.put(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, _('You do not have permission to perform this action.'))

    def test_put_request_on_brand_collection_view_uses_custom_model_form(self):
        brand = self.create_brand()
        data = simplejson.dumps({
            'name': 'this should give an error',
        })
        url = reverse('backbone:tests_brand_detail', args=[brand.id])
        response = self.client.put(url, data, content_type='application/json')
        self.assertEqual(Product.objects.count(), 0)
        data = self.parseJsonResponse(response, status_code=400)
        self.assertEqual(len(data), 1)
        self.assertEqual(data['name'], [_('Brand name must start with a capital letter.')])


class DeleteTests(TestHelper):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test', email='t@t.com')
        self.client.login(username='test', password='test')
        delete_product = Permission.objects.get_by_natural_key('delete_product', 'tests', 'product')
        delete_brand = Permission.objects.get_by_natural_key('delete_brand', 'tests', 'brand')
        self.user.user_permissions.add(delete_product, delete_brand)

    def test_delete_request_on_product_deletes_the_item(self):
        product = self.create_product()
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Product.objects.count(), 0)

    def test_delete_request_on_product_when_user_not_logged_in_returns_403(self):
        self.client.logout()
        product = self.create_product()
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, _('You do not have permission to perform this action.'))
        self.assertEqual(Product.objects.count(), 1)

    def test_delete_request_on_product_when_user_doesnt_have_delete_permission_returns_403(self):
        self.client.logout()
        self.user.user_permissions.clear()
        self.client.login(username='test', password='test')
        product = self.create_product()
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, _('You do not have permission to perform this action.'))
        self.assertEqual(Product.objects.count(), 1)

    def test_delete_request_on_brand_returns_403(self):
        brand = self.create_brand()
        url = reverse('backbone:tests_brand_detail', args=[brand.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, _('You do not have permission to perform this action.'))
        self.assertEqual(Brand.objects.count(), 1)
