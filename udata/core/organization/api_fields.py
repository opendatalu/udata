# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata.api import api, fields, base_reference
from udata.core.badges.api import badge_fields

from udata.i18n import lazy_gettext as _

from .models import ORG_ROLES, MEMBERSHIP_STATUS


org_ref_fields = api.inherit('OrganizationReference', base_reference, {
    'name': fields.String(description=_('The organization name'), readonly=True),
    'acronym': fields.String(description=_('The organization acronym')),
    'uri': fields.UrlFor(
        'api.organization', lambda o: {'org': o},
        description=_('The organization API URI'), readonly=True),
    'slug': fields.String(
        description=_('The organization string used as permalink'),
        required=True),
    'page': fields.UrlFor(
        'organizations.show', lambda o: {'org': o},
        description=_('The organization web page URL'), readonly=True),
    'logo': fields.ImageField(
        size=100, description=_('The organization logo URL')),
})


from udata.core.user.api_fields import user_ref_fields  # noqa: required

request_fields = api.model('MembershipRequest', {
    'id': fields.String(readonly=True),
    'user': fields.Nested(user_ref_fields),
    'created': fields.ISODateTime(
        description=_('The request creation date'), readonly=True),
    'status': fields.String(
        description=_('The current request status'), required=True,
        enum=MEMBERSHIP_STATUS.keys()),
    'comment': fields.String(
        description=_('A request comment from the user'), required=True),
})

member_fields = api.model('Member', {
    'user': fields.Nested(user_ref_fields),
    'role': fields.String(
        description=_('The member role in the organization'), required=True,
        enum=ORG_ROLES.keys())
})

org_fields = api.model('Organization', {
    'id': fields.String(
        description=_('The organization identifier'), required=True),
    'name': fields.String(description=_('The organization name'), required=True),
    'acronym': fields.String(description=_('The organization acronym')),
    'url': fields.String(description=_('The organization website URL')),
    'slug': fields.String(
        description=_('The organization string used as permalink'),
        required=True),
    'description': fields.Markdown(
        description=_('The organization description in Markdown'), required=True),
    'created_at': fields.ISODateTime(
        description=_('The organization creation date'), readonly=True),
    'last_modified': fields.ISODateTime(
        description=_('The organization last modification date'), readonly=True),
    'deleted': fields.ISODateTime(
        description=_('The organization deletion date if deleted'),
        readonly=True),
    'metrics': fields.Raw(
        description=_('The organization metrics'), readonly=True),
    'uri': fields.UrlFor(
        'api.organization', lambda o: {'org': o},
        description=_('The organization API URI'), readonly=True),
    'page': fields.UrlFor(
        'organizations.show', lambda o: {'org': o},
        description=_('The organization page URL'), readonly=True),
    'logo': fields.ImageField(description=_('The organization logo URLs')),
    'members': fields.List(
        fields.Nested(member_fields, description=_('The organization members'))),
    'badges': fields.List(fields.Nested(badge_fields),
                          description=_('The organization badges'),
                          readonly=True),
})

org_page_fields = api.model('OrganizationPage', fields.pager(org_fields))

org_suggestion_fields = api.model('OrganizationSuggestion', {
    'id': fields.String(
        description=_('The organization identifier'), readonly=True),
    'name': fields.String(description=_('The organization name'), readonly=True),
    'acronym': fields.String(
        description=_('The organization acronym'), readonly=True),
    'slug': fields.String(
        description=_('The organization permalink string'), readonly=True),
    'image_url': fields.String(
        description=_('The organization logo URL'), readonly=True),
    'page': fields.UrlFor(
        'organizations.show_redirect', lambda o: {'org': o['slug']},
        description=_('The organization web page URL'), readonly=True),
    'score': fields.Float(
        description=_('The internal match score'), readonly=True),
})

refuse_membership_fields = api.model('RefuseMembership', {
    'comment': fields.String(
        description=_('The refusal comment.')),
})
