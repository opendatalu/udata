from udata.i18n import lazy_gettext as _

REUSE_TYPES = {
    "api": _("API"),
    "application": _("Application"),
    "idea": _("Idea"),
    "news_article": _("News Article"),
    "paper": _("Paper"),
    "post": _("Post"),
    "visualization": _("Visualization"),
    "hardware": _("Connected device"),
}

REUSE_TOPICS = {
    'affaires-internationales': _('International matters'),
    'agriculture': _('Agriculture'),
    'droit': _('Justice, Law and Public Order'),
    'economie': _('Economy and Finance'),
    'energie': _('Energy and natural resources'),
    'entreprises': _('Entreprises'),
    'environnement': _('Environment and Climate'),
    'gouvernement-et-secteur-public': _('Government and public sector'),
    'population-et-societe': _('Population and society'),
    'regions-et-developement-local': _('Regions and local development'),
    'sante': _('Health'),
    'science-et-technologie': _('Science and Technology'),
    'transports-charging-points': _('Transport - Charging points'),
    'transports-idacs': _('Transport - IDACS'),
    'transports': _('Transport'),
    'vie-quotidienne': _('Education, culture and sport'),
    'donnees-geospatiales': _('Geospatial data'),
    'observation-de-la-terre-et-environnement': _('Earth observation and environment'),
    'meteo': _('Meteorological data'),
    'statistiques': _('Statistics'),
    'mobilite': _('Mobility'),
    'others': _('Others'),
}


IMAGE_SIZES = [500, 100, 50, 25]
IMAGE_MAX_SIZE = 800

TITLE_SIZE_LIMIT = 350
DESCRIPTION_SIZE_LIMIT = 100000
