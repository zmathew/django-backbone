import datetime
from decimal import Decimal
import json

from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.translation import ugettext as _

from backbone.tests.models import Product, Brand, Category, ExtendedProduct, DisplayFieldsProduct
from backbone.tests.backbone_api import BrandBackboneView


class TestHelper(TestCase):

    def parseJsonResponse(self, response, status_code=200):
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = json.loads(response.content)
        return data

    def create_product(self, **kwargs):
        defaults = {
            'name': 'Test Product',
            'price': '12.32',
            'sku': '12345678',
        }
        if 'brand' not in kwargs:
            defaults['brand'] = self.create_brand()
        defaults.update(kwargs)
        return Product.objects.create(**defaults)

    def create_extended_product(self, **kwargs):
        defaults = {
            'name': 'Test Product',
            'price': '12.32'
        }
        if 'brand' not in kwargs:
            defaults['brand'] = self.create_brand()
        defaults.update(kwargs)
        return ExtendedProduct.objects.create(**defaults)

    def create_displayfields_product(self, **kwargs):
        defaults = {
            'name': 'Beta Product',
            'price': '13.32'
        }
        if 'brand' not in kwargs:
            defaults['brand'] = self.create_brand()
        defaults.update(kwargs)
        return DisplayFieldsProduct.objects.create(**defaults)

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

        expected_fields = [
            'id', 'creation_date', 'name', 'brand', 'categories', 'price', 'order',
            'is_priced_under_10', 'get_first_category_id', 'sku', 'custom2'
        ]
        self.assertEqual(set(expected_fields), set(fields))
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

    def test_collection_view_put_request_returns_403(self):
        url = reverse('backbone:tests_product')
        response = self.client.put(url)
        self.assertEqual(response.status_code, 403)

    def test_collection_view_delete_request_returns_403(self):
        url = reverse('backbone:tests_product')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_collection_view_pagination(self):
        # Brand is paginated 2 per page
        p1 = self.create_brand()
        p2 = self.create_brand()
        p3 = self.create_brand()

        url = reverse('backbone:tests_brand')

        # First page
        response = self.client.get(url, {'page': 1})
        data = self.parseJsonResponse(response)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['id'], p1.id)
        self.assertEqual(data[1]['id'], p2.id)

        # Second Page
        response = self.client.get(url, {'page': 2})
        data = self.parseJsonResponse(response)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], p3.id)

    def test_collection_view_page_parameter_out_of_range_returns_error(self):
        url = reverse('backbone:tests_brand')

        response = self.client.get(url, {'page': 2})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, _('Invalid `page` parameter: Out of range.'))

    def test_collection_view_page_parameter_not_an_integer_returns_error(self):
        url = reverse('backbone:tests_brand')

        response = self.client.get(url, {'page': 'abcd'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, _('Invalid `page` parameter: Not a valid integer.'))

    def test_collection_view_that_is_not_paginated_ignores_page_parameter(self):
        url = reverse('backbone:tests_product')
        response = self.client.get(url, {'page': 999})
        self.assertEqual(response.status_code, 200)

    def test_collection_view_for_view_with_custom_url_slug(self):
        brand = self.create_brand()
        url = reverse('backbone:tests_brand_alternate')
        response = self.client.get(url)
        data = self.parseJsonResponse(response)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], brand.id)
        self.assertEqual(data[0]['custom'], 'foo')


class DetailTests(TestHelper):

    def test_detail_view_returns_object_details(self):
        product = self.create_product(price=3)
        category = self.create_category()
        product.categories.add(category)

        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.get(url)
        data = self.parseJsonResponse(response)
        self.assertEqual(data['id'], product.id)
        self.assertEqual(data['name'], product.name)
        self.assertEqual(data['brand'], product.brand.id)
        self.assertEqual(data['categories'], [category.id])
        self.assertEqual(data['price'], str(product.price))
        self.assertEqual(data['order'], product.order)
        # Attribute on model
        self.assertEqual(data['is_priced_under_10'], True)
        # Callable
        self.assertEqual(data['sku'], '#: %s' % product.sku)
        # Callable on admin class
        self.assertEqual(data['custom2'], 'custom2: %s' % product.name)
        # Callable on model
        self.assertEqual(data['get_first_category_id'], category.id)

    def test_detail_view_uses_display_detail_fields_when_defined(self):
        display_fields_product = self.create_displayfields_product(price=111)
        category = self.create_category()
        display_fields_product.categories.add(category)

        url = reverse('backbone:tests_displayfieldsproduct_detail', args=[display_fields_product.id])
        response = self.client.get(url)
        data = self.parseJsonResponse(response)

        self.assertEqual(data['id'], display_fields_product.id)
        self.assertEqual(data['name'], display_fields_product.name)
        self.assertEqual(data['brand'], display_fields_product.brand.id)
        self.assertEqual(data['categories'], [category.id])
        self.assertTrue('price' not in data)
        self.assertTrue('order' not in data)
        # Attribute on model
        self.assertTrue('is_priced_under_10' not in data)
        # Callable
        self.assertTrue('sku' not in data)
        # Callable on admin class
        self.assertTrue('custom2' not in data)
        # Callable on model
        self.assertTrue('get_first_category_id' not in data)
        self.assertEqual(len(data.keys()), 4)

    def test_collection_view_uses_display_collection_fields_when_defined(self):
        display_fields_product = self.create_displayfields_product(price=111)
        category = self.create_category()
        display_fields_product.categories.add(category)

        url = reverse('backbone:tests_displayfieldsproduct')
        response = self.client.get(url)
        data = self.parseJsonResponse(response)

        self.assertEqual(len(data), 1)

        data = data[0]
        self.assertEqual(data['id'], display_fields_product.id)
        self.assertEqual(data['name'], display_fields_product.name)
        self.assertEqual(data['brand'], display_fields_product.brand.id)
        self.assertEqual(data['categories'], [category.id])
        self.assertTrue('price' not in data)
        self.assertTrue('order' not in data)
        # Attribute on model
        self.assertTrue('is_priced_under_10' not in data)
        # Callable
        self.assertTrue('sku' not in data)
        # Callable on admin class
        self.assertTrue('custom2' not in data)
        # Callable on model
        self.assertTrue('get_first_category_id' not in data)
        self.assertEqual(len(data.keys()), 4)

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

    def test_detail_view_post_request_returns_403(self):
        product = self.create_product()
        url = reverse('backbone:tests_product_detail', args=[product.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_detail_view_for_view_with_custom_url_slug(self):
        brand = self.create_brand()
        url = reverse('backbone:tests_brand_alternate_detail', args=[brand.id])
        response = self.client.get(url)
        data = self.parseJsonResponse(response)
        self.assertEqual(data['id'], brand.id)
        self.assertEqual(data['custom'], 'foo')


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
        data = json.dumps({
            'name': 'Test',
            'brand': brand.id,
            'categories': [cat1.id, cat2.id],
            'price': 12.34,
            'order': 1,
            'sale_date': '2006-10-25 14:30:59',
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
        self.assertEqual(product.sale_date, datetime.datetime(2006, 10, 25, 14, 30, 59))

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
        response = self.client.post(url, 'Some invalid json', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, _('Unable to parse JSON request body.'))

    def test_post_request_on_product_collection_view_with_validation_errors_returns_error_list_as_json(self):
        data = json.dumps({
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
        data = json.dumps({
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
        data = json.dumps({
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
        data = json.dumps({
            'name': 'this should give an error',
        })
        url = reverse('backbone:tests_brand')
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(Brand.objects.count(), 0)
        data = self.parseJsonResponse(response, status_code=400)
        self.assertEqual(len(data), 1)
        self.assertEqual(data['name'], [_('Brand name must start with a capital letter.')])

    def test_post_request_on_custom_url_slug_view_contains_custom_url_in_location_header(self):
        data = json.dumps({
            'name': 'Foo',
        })
        url = reverse('backbone:tests_brand_alternate')
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Brand.objects.count(), 1)

        self.assertEqual(
            response['Location'],
            'http://testserver' + reverse(
                'backbone:tests_brand_alternate_detail', args=[Brand.objects.get().id]
            )
        )


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
        data = json.dumps({
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
        data = json.dumps({
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
        data = json.dumps({
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
        data = json.dumps({
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
        data = json.dumps({
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


class InheritanceTests(TestHelper):

    def test_detail_view_returns_inherited_object_details(self):
        ext_product = self.create_extended_product(price=9)
        category = self.create_category()
        ext_product.categories.add(category)

        url = reverse('backbone:tests_extendedproduct_detail', args=[ext_product.id])
        response = self.client.get(url)
        data = self.parseJsonResponse(response)
        self.assertEqual(data['id'], ext_product.id)
        self.assertEqual(data['name'], ext_product.name)
        self.assertEqual(data['brand'], ext_product.brand.id)
        self.assertEqual(data['categories'], [category.id])
        self.assertEqual(data['price'], str(ext_product.price))
        self.assertEqual(data['order'], ext_product.order)
        self.assertEqual(data['description'], ext_product.description)
        # Attribute on model
        self.assertEqual(data['is_priced_under_10'], True)
        # Callable on model
        self.assertEqual(data['get_first_category_id'], category.id)


class InvalidViewTests(TestHelper):
    def setUp(self):
        BrandBackboneView.display_fields += ['invalid_field']

    def tearDown(self):
        BrandBackboneView.display_fields.remove('invalid_field')

    def test_invalid_field_name_raises_attribute_error(self):
        brand = self.create_brand()
        url = reverse('backbone:tests_brand_detail', args=[brand.id])
        try:
            self.client.get(url)
        except AttributeError, err:
            self.assertEqual(str(err), "Invalid field: invalid_field")
