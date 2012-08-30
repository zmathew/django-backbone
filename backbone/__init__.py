"""Provides AJAX file upload functionality for FileFields and ImageFields with a simple widget replacement in the form."""

from backbone.sites import BackboneSite


VERSION = (0, 1, 0)

__version__ = '.'.join(map(str, VERSION))


site = BackboneSite()


def autodiscover():
    """
    Auto-discover INSTALLED_APPS backbone_api.py modules.
    """
    # This code is based off django.contrib.admin.__init__
    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        # Attempt to import the app's backbone module.
        try:
            import_module('%s.backbone_api' % app)
        except:
            # Decide whether to bubble up this error. If the app just
            # doesn't have an backbone module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, 'backbone_api'):
                raise
