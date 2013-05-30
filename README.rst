===============
django-backbone
===============


Overview
--------
This app provides a Backbone.js compatible REST API for your models. It follows the Django admin pattern of extending, overriding and registering; and provides an extendable class based view for customization.

This way you can have quick, out-of-the-box functionality or you can override any method or variable to customize things to your liking.

For example:
::

    # fooapp/backbone_api.py
    import backbone
    from fooapp.models import Foo

    class FooAPIView(backbone.views.BackboneAPIView):
        model = Foo
        display_fields = ('title', 'description')
        ordering = ('creation_date', 'id')

    backbone.site.register(FooAPIView)


More advanced customization can be accomplished by hooking into methods on the inherited class - which itself is a class based view. For example:
::

    ...

    class FooAPIView(backbone.views.BackboneAPIView):
        model = Foo
        display_fields = ('title', 'description',)
        ordering = ('creation_date', 'id')

        def post(self, request):
            return HttpResponseForbidden('No adding allowed!')

        def queryset(self, request):
            # Only return "active" objects
            return Foo.objects.filter(is_active=True).order_by('-id')

        def has_delete_permission(request, obj):
            return request.user.is_staff  # Only staff can delete objects
    ...


Features
--------
* Automatically generates a JSON REST API for your models that works nicely with Backbone.js.
* API based on class based views and model forms allowing for fine-grained customization and extensibility.
* Customizable permission restrictions. By default it uses ``django.contrib.auth`` authentication and permissions (similar to Django admin).


Usage
-----
#. Create a ``backbone_api.py`` file in your app folder and register your API definitions by subclassing ``backbone.views.BackboneAPIView``.
    ::

        # fooapp/backbone_api.py
        import backbone
        from fooapp.models import Foo

        class FooAPIView(backbone.views.BackboneAPIView):
            model = Foo
            display_fields = ('title', 'description')
            ordering = ('creation_date', 'id')

        backbone.site.register(FooAPIView)

        See section on 'BackboneAPIView Options' for a full list of options available.

#. In your Javascript collection/model definitions, set the ``url``/``urlRoot`` to point to the ``django-backbone`` API:
    ::

        // Assuming you have a Backbone model called 'Foo' and a collection 'FooCollection'
        Foo.prototype.urlRoot = "{% url 'backbone:fooapp_foo' %}";
        FooCollection.prototype.url = "{% url 'backbone:fooapp_foo' %}";

        See section on 'URL reversing' below for details on the url naming.

#. (Optional) If your have csrf protection turned on, you'll need to modify the Backbone.sync command to send the csrf token:
    ::

        <script>
            // (Optional) Do this if you are using csrf protection:
            // See: https://docs.djangoproject.com/en/dev/ref/contrib/csrf/
            var oldSync = Backbone.sync;
            Backbone.sync = function(method, model, options) {
                options.beforeSend = function(xhr){
                    xhr.setRequestHeader('X-CSRFToken', '{{ csrf_token }}');
                };
                return oldSync(method, model, options);
            };
        </script>

#. That's it. You should now be able to perform ``fetch()``, ``save()``, etc. on your Backbone collections and models.


Permissions
'''''''''''

By default, ``django-backbone`` prevents add, update or delete requests unless the user is logged in and has the ``can_add``, ``can_change`` or ``can_delete`` permission (respectively). This follows the permissions used in the Django admin, with one exception - **read access is permitted** publicly on all registered models.

This can be changed by overriding the appropriate permission hooks (see section '``BackboneAPIView`` Options').


``BackboneAPIView`` Options
'''''''''''''''''''''''''''

Please check out the source code of the class ``backbone.views.BackboneAPIView`` for the full list of hooks. The methods are documented by their docstrings.

Here are some basic options that you can customize:

* ``model``: The model to be used for this API definition
* ``display_fields``: Fields to return for read (GET) requests,
* ``fields``: Fields to allow when adding (POST) or editing (PUT) objects.
* ``form``: The form class to be used for adding or editing objects.
* ``ordering``: Ordering used when retrieving the collection
* ``paginate_by``: The max number of objects per page (enables use of the ``page`` GET parameter).


Reversing the API urls
''''''''''''''''''''''

The following named URL patterns are provided for all models that are registered:

* Collection URL: ``backbone:<app_name>_<model_name>`` (reverses to ``/<app_name>/<model_name>/``)
* Model URL: ``backbone:<app_name>_<model_name>_detail`` (reverses to ``/<app_name>/<model_name>/<object_id>``)

You can change the ``<model_name>`` in the url (and url name) by specifying the ``url_slug`` attribute on the ``BackboneView`` class (just be sure it doesn't collide with another view).



Installation
------------
Note: ``django-backbone`` requires Django 1.3 or higher.

#. Add ``backbone`` to ``INSTALLED_APPS`` in your settings file.
#. Hook in the urls and call ``backbone.autodiscover()`` (which will find all ``backbone_api.py`` files in your apps):
    ::

        # urls.py

        import backbone
        backbone.autodiscover()

        urlpatterns += patterns('',
            (r'^backbone/', include(backbone.site.urls)),
        )



Running the tests
-----------------
::

    ./manage.py test tests --settings=backbone.tests.settings



Alternatives/Inspiration
------------------------
This app borrows concepts and patterns from other open source Django/Backbone integration apps. It's worth having a look at them as they may be better suited depending on your use case:

* `djangbone <https://github.com/af/djangbone>`_: Light weight, simliar concept using class based views.
* `backbone-tastypie <https://github.com/PaulUithol/backbone-tastypie>`_: A little heavier as it uses `django-tastypie <https://github.com/toastdriven/django-tastypie>`_ which can provide some powerful API features such as throttling and caching.


License
-------
This app is licensed under the BSD license. See the LICENSE file for details.
