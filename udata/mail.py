import logging
from contextlib import contextmanager

from blinker import signal

from flask import current_app, render_template
from flask_mail import Mail, Message as _Message

from email.utils import make_msgid
class Message(_Message):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # RFC 2822 does not allow over 78 long Message-ID header or it flags as spam.
        # AWS servers generate way too large hostnames.
        # flask_mail has not method to pass the domain argument to make_msgid, so we have to overload the Message class
        self.msgId = make_msgid(domain="data.public.lu") # Improvement: set from a variable in udata.cfg

from udata import i18n


log = logging.getLogger(__name__)

mail = Mail()

mail_sent = signal('mail-sent')


class FakeMailer(object):
    '''Display sent mail in logging output'''
    def send(self, msg):
        log.debug(msg.body)
        log.debug(msg.html)
        mail_sent.send(msg)


@contextmanager
def dummyconnection(*args, **kw):
    """Allow to test email templates rendering without actually send emails."""
    yield FakeMailer()


def init_app(app):
    mail.init_app(app)


def send(subject, recipients, template_base, **kwargs):
    '''
    Send a given email to multiple recipients.

    User prefered language is taken in account.
    To translate the subject in the right language, you should ugettext_lazy
    '''
    sender = kwargs.pop('sender', None)
    if not isinstance(recipients, (list, tuple)):
        recipients = [recipients]

    tpl_path = f'mail/{template_base}'

    debug = current_app.config.get('DEBUG', False)
    send_mail = current_app.config.get('SEND_MAIL', not debug)
    connection = send_mail and mail.connect or dummyconnection

    with connection() as conn:
        for recipient in recipients:
            lang = i18n._default_lang(recipient)
            with i18n.language(lang):
                log.debug(
                    'Sending mail "%s" to recipient "%s"', subject, recipient)
                msg = Message(subject, sender=sender,
                              recipients=[recipient.email])
                msg.body = render_template(
                    f'{tpl_path}.txt', subject=subject,
                    sender=sender, recipient=recipient, **kwargs)
                msg.html = render_template(
                    f'{tpl_path}.html', subject=subject,
                    sender=sender, recipient=recipient, **kwargs)
                conn.send(msg)
