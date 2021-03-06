# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata.api import api, fields, base_reference

from udata.core.badges.api import badge_fields
from udata.core.dataset.api_fields import dataset_ref_fields
from udata.core.organization.api_fields import org_ref_fields
from udata.core.user.api_fields import user_ref_fields

from udata.i18n import lazy_gettext as _

from .models import REUSE_TYPES


reuse_fields = api.model('Reuse', {
    'id': fields.String(description=_('The reuse identifier'), readonly=True),
    'title': fields.String(description=_('The reuse title'), required=True),
    'slug': fields.String(
        description=_('The reuse permalink string'), readonly=True),
    'type': fields.String(
        description=_('The reuse type'), required=True, enum=REUSE_TYPES.keys()),
    'url': fields.String(
        description=_('The reuse remote URL (website)'), required=True),
    'description': fields.Markdown(
        description=_('The reuse description in Markdown'), required=True),
    'tags': fields.List(
        fields.String, description=_('Some keywords to help in search')),
    'badges': fields.List(fields.Nested(badge_fields),
                          description=_('The reuse badges'),
                          readonly=True),
    'featured': fields.Boolean(
        description=_('Is the reuse featured'), readonly=True),
    'private': fields.Boolean(
        description=_('Is the reuse private to the owner or the organization')),
    'image': fields.ImageField(description=_('The reuse thumbnail')),
    'created_at': fields.ISODateTime(
        description=_('The reuse creation date'), readonly=True),
    'last_modified': fields.ISODateTime(
        description=_('The reuse last modification date'), readonly=True),
    'deleted': fields.ISODateTime(
        description=_('The organization identifier'), readonly=True),
    'datasets': fields.List(
        fields.Nested(dataset_ref_fields), description=_('The reused datasets')),
    'organization': fields.Nested(
        org_ref_fields, allow_null=True,
        description=_('The publishing organization'), readonly=True),
    'owner': fields.Nested(
        user_ref_fields, description=_('The owner user'), readonly=True,
        allow_null=True),
    'metrics': fields.Raw(description=_('The reuse metrics'), readonly=True),
    'uri': fields.UrlFor(
        'api.reuse', lambda o: {'reuse': o},
        description=_('The reuse API URI'), readonly=True),
    'page': fields.UrlFor(
        'reuses.show', lambda o: {'reuse': o},
        description=_('The reuse page URL'), readonly=True),
})

reuse_page_fields = api.model('ReusePage', fields.pager(reuse_fields))

reuse_suggestion_fields = api.model('ReuseSuggestion', {
    'id': fields.String(description=_('The reuse identifier'), readonly=True),
    'title': fields.String(description=_('The reuse title'), readonly=True),
    'slug': fields.String(
        description=_('The reuse permalink string'), readonly=True),
    'image_url': fields.String(description=_('The reuse thumbnail URL')),
    'page': fields.UrlFor(
        'reuses.show_redirect', lambda o: {'reuse': o['slug']},
        description=_('The reuse page URL'), readonly=True),
    'score': fields.Float(
        description=_('The internal match score'), readonly=True),
})


reuse_ref_fields = api.inherit('ReuseReference', base_reference, {
    'title': fields.String(description=_('The reuse title'), readonly=True),
    'image': fields.ImageField(description=_('The reuse thumbnail')),
    'uri': fields.UrlFor(
        'api.reuse', lambda o: {'reuse': o},
        description=_('The reuse API URI'), readonly=True),
    'page': fields.UrlFor(
        'reuses.show', lambda o: {'reuse': o},
        description=_('The reuse page URL'), readonly=True),
})

reuse_type_fields = api.model('ReuseType', {
    'id': fields.String(description=_('The reuse type identifier')),
    'label': fields.String(description=_('The reuse type display name'))
})
