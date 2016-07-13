# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata.api import api, fields, base_reference

from udata.i18n import lazy_gettext as _


user_ref_fields = api.inherit('UserReference', base_reference, {
    'first_name': fields.String(
        description=_('The user first name'), readonly=True),
    'last_name': fields.String(
        description=_('The user larst name'), readonly=True),
    'slug': fields.String(
        description=_('The user permalink string'), required=True),
    'page': fields.UrlFor(
        'users.show', lambda u: {'user': u},
        description=_('The user profile page URL'), readonly=True),
    'uri': fields.UrlFor(
        'api.user', lambda o: {'user': o},
        description=_('The user API URI'), required=True),
    'avatar': fields.ImageField(size=100, description=_('The user avatar URL')),
})


from udata.core.organization.api_fields import org_ref_fields  # noqa

user_fields = api.model('User', {
    'id': fields.String(
        description=_('The user identifier'), required=True),
    'slug': fields.String(
        description=_('The user permalink string'), required=True),
    'first_name': fields.String(
        description=_('The user first name'), required=True),
    'last_name': fields.String(
        description=_('The user last name'), required=True),
    'avatar': fields.ImageField(description=_('The user avatar URL')),
    'website': fields.String(description=_('The user website')),
    'about': fields.Markdown(description=_('The user self description')),
    'roles': fields.List(fields.String, description=_('Site wide user roles')),
    'organizations': fields.List(
        fields.Nested(org_ref_fields),
        description=_('The organization the user belongs to')),
    'since': fields.ISODateTime(
        attribute='created_at',
        description=_('The registeration date'), required=True),
    'page': fields.UrlFor(
        'users.show', lambda u: {'user': u},
        description=_('The user profile page URL'), readonly=True),
    'uri': fields.UrlFor(
        'api.user', lambda o: {'user': o},
        description=_('The user API URI'), required=True),
})

me_fields = api.inherit('Me', user_fields, {
    'email': fields.String(description=_('The user email'), required=True),
    'apikey': fields.String(description=_('The user API Key'), readonly=True),
})

me_metrics_fields = api.model('MyMetrics', {
    'id': fields.String(
        description=_('The user identifier'), required=True),
    'resources_availability': fields.Float(
        description=_("The user's resources availability percentage"),
        readonly=True),
    'datasets_org_count': fields.Integer(
        description=_("The user's orgs datasets number"), readonly=True),
    'followers_org_count': fields.Integer(
        description=_("The user's orgs followers number"), readonly=True),
    'datasets_count': fields.Integer(
        description=_("The user's datasets number"), readonly=True),
    'followers_count': fields.Integer(
        description=_("The user's followers number"), readonly=True),
})

apikey_fields = api.model('ApiKey', {
    'apikey': fields.String(description=_('The user API Key'), readonly=True),
})

user_page_fields = api.model('UserPage', fields.pager(user_fields))

user_suggestion_fields = api.model('UserSuggestion', {
    'id': fields.String(description=_('The user identifier'), readonly=True),
    'first_name': fields.String(description=_('The user first name'),
                                readonly=True),
    'last_name': fields.String(description=_('The user last name'),
                               readonly=True),
    'avatar_url': fields.String(description=_('The user avatar URL')),
    'slug': fields.String(
        description=_('The user permalink string'), readonly=True),
    'score': fields.Float(
        description=_('The internal match score'), readonly=True),
})


notifications_fields = api.model('Notification', {
    'type': fields.String(description=_('The notification type'), readonly=True),
    'created_on': fields.ISODateTime(
        description=_('The notification creation datetime'), readonly=True),
    'details': fields.Raw(
        description=_('Key-Value details depending on notification type'),
        readonly=True)
})
