class BackboneSite(object):

    def __init__(self, name='backbone'):
        self._registry = []
        self.name = name

    def register(self, backbone_view_class):
        """
        Registers the given backbone view class.
        """
        if backbone_view_class not in self._registry:
            self._registry.append(backbone_view_class)

    def unregister(self, backbone_view_class):
        if backbone_view_class in self._registry:
            self._registry.remove(backbone_view_class)

    def get_urls(self):
        try:
            from django.conf.urls import patterns, url
        except ImportError:  # For backwards compatibility with Django <=1.3
            from django.conf.urls.defaults import patterns, url

        urlpatterns = patterns('')
        for view_class in self._registry:
            app_label = view_class.model._meta.app_label
            url_slug = view_class.url_slug or view_class.model._meta.module_name

            url_path_prefix = r'^%s/%s' % (app_label, url_slug)
            base_url_name = '%s_%s' % (app_label, url_slug)

            urlpatterns += patterns('',
                url(url_path_prefix + '$', view_class.as_view(), name=base_url_name),
                url(url_path_prefix + '/(?P<id>\d+)$', view_class.as_view(),
                    name=base_url_name + '_detail')
            )
        return urlpatterns

    @property
    def urls(self):
        return (self.get_urls(), 'backbone', self.name)
