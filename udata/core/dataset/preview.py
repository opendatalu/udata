import warnings
import logging
from abc import ABC, abstractmethod

from flask import current_app

from udata import entrypoints
from udata.app import cache

# Cache available plugins for a day
# Don't forget to flush cache on new configuration or plugin
CACHE_DURATION = 60 * 60 * 24
CACHE_KEY = 'udata.preview.enabled_plugins'


log = logging.getLogger(__name__)



class PreviewWarning(UserWarning):
    pass


class PreviewPlugin(ABC):
    '''
    An abstract preview plugin.

    In order to register a functionnal PreviewPlugin,
    extension developpers need to:
    - inherit this class
    - implement abstract methods
    - expose the class on the ``udata.preview`` endpoint
    '''
    #: Default previews are given only if no specific preview match.
    #: Typically plugins only relying on mimetype or format
    #: should have `fallback = True`
    fallback = False

    @abstractmethod
    def can_preview(self, resource):
        '''
        Whether or not this plugin can provide a preview for the given resource

        :param ResourceMixin resource: the (community) resource to preview
        :return: ``True`` if this plugin can provide a preview
        :rtype: bool
        '''
        pass

    @abstractmethod
    def preview_url(self, resource):
        '''
        Returns the absolute preview URL associated to the resource

        :param ResourceMixin resource: the (community) resource to preview
        :return: a preview url to be displayed into an iframe or a new window
        :rtype: str
        '''
        pass


@cache.cached(timeout=CACHE_DURATION, key_prefix=CACHE_KEY)
def get_enabled_plugins():
    '''
    Returns enabled preview plugins.

    Plugins are sorted, defaults come last
    '''
    plugins = entrypoints.get_enabled('udata.preview', current_app).values()
    log.warning(plugins)

    valid = [p for p in plugins if issubclass(p, PreviewPlugin)]
    for plugin in plugins:
        if plugin not in valid:
            clsname = plugin.__name__
            msg = '{0} is not a valid preview plugin'.format(clsname)
            warnings.warn(msg, PreviewWarning)
    return [p() for p in sorted(valid, key=lambda p: 1 if p.fallback else 0)]


def get_preview_url(resource):
    '''
    Returns the most pertinent preview URL associated to the resource, if any.

    :param ResourceMixin resource: the (community) resource to preview
    :return: a preview url to be displayed into an iframe or a new window
    :rtype: HttpResponse
    '''

    for p in get_enabled_plugins():
        can_preview = "yes" if p.can_preview() else "no"
        url = p.preview_url(resource) if p.can_preview() else "-"
        log.warning("Enabled plugin: %s, can preview: %s, url: %s" % (str(p), can_preview, url))

    candidates = (p.preview_url(resource)
                  for p in get_enabled_plugins()
                  if p.can_preview(resource))
    return next(iter(candidates), None)
