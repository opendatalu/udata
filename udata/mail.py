import logging
from contextlib import contextmanager
from smtplib import SMTPException

from blinker import signal
from flask import current_app, render_template
from flask_mail import Mail, Message

from udata import i18n
from typing import Set

log = logging.getLogger(__name__)

mail = Mail()

mail_sent = signal("mail-sent")


class FakeMailer(object):
    """Display sent mail in logging output"""

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


def send(subject, recipients, template_base, render_fn=render_template, **kwargs):
    '''
    Send a given email to multiple recipients.

    User prefered language is taken in account.
    To translate the subject in the right language, you should ugettext_lazy
    '''
    sender = kwargs.pop('sender', None)
    reply_to = kwargs.pop('reply_to', sender)
    if not isinstance(recipients, (list, tuple)):
        recipients = [recipients]

    tpl_path = f"mail/{template_base}"

    debug = current_app.config.get("DEBUG", False)
    send_mail = current_app.config.get("SEND_MAIL", not debug)
    connection = send_mail and mail.connect or dummyconnection

    with connection() as conn:
        for recipient in recipients:
            lang = i18n._default_lang(recipient)

            # we allow str just in case we want to send to an email address without it being an user
            recipient_email = recipient.email if not isinstance(recipient, str) else recipient

            with i18n.language(lang):
                log.debug(
                    'Sending mail "%s" to recipient "%s"', subject, recipient)
                msg = Message(subject, sender=sender,
                              recipients=[recipient_email], reply_to=reply_to)
                msg.body = render_fn(
                    f'{tpl_path}.txt', subject=subject,
                    sender=sender, recipient=recipient, **kwargs)
                msg.html = render_fn(
                    f'{tpl_path}.html', subject=subject,
                    sender=sender, recipient=recipient, **kwargs)
                try:
                    conn.send(msg)
                except SMTPException as e:
                    log.error(f'Error sending mail {e}')


