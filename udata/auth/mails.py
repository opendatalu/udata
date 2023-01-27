import logging
import email_validator
from flask import current_app
from udata.tasks import task
from udata.patch.mail import Message

log = logging.getLogger(__name__)


@task
def sendmail(msg):
    debug = current_app.config.get('DEBUG', False)
    send_mail = current_app.config.get('SEND_MAIL', not debug)
    if send_mail:
        mail = current_app.extensions.get("mail")
        mail.send(msg)


class UdataMailUtil:
    """
    A rework of the udata-security MailUtil passed on flask-security unit
    send_mail is called by flask-security
    https://github.com/Flask-Middleware/flask-security/blob/master/flask_security/mail_util.py

    The sender is in the udata.cfg as SECURITY_EMAIL_SENDER
    This variable name is (?) passed to flask-security
    https://flask-security-too.readthedocs.io/en/stable/configuration.html#SECURITY_EMAIL_SENDER

    Other mails may be sent by ../mail.py 
    """

    def __init__(self, app):
        self.app = app

    def send_mail(self, template, subject, recipient, sender, body, html, user, **kwargs):
        # In Flask-Mail, sender can be a two element tuple -- (name, address)
        if isinstance(sender, tuple) and len(sender) == 2:
            sender = (str(sender[0]), str(sender[1]))
        else:
            sender = str(sender)

        # sender at this point seems problematic, add debug and overwrite it for now
        log.info("Send mail to %s" % str(sender))
        sender = self.app.config.get('MAIL_DEFAULT_SENDER', ('Portail Open Data', 'info@data.public.lu'))

        msg = Message(subject, sender=sender, recipients=[recipient])
        msg.body = body
        msg.html = html

        sendmail.delay(msg)

    def normalize(self, email):
        """
        Called at registration and login
        Calls validate method with deliverability check disabled to prevent
        login failure for existing users without a valid email domain name
        """
        return self.validate(email, validation_args={"check_deliverability": False})

    def validate(self, email, validation_args=None):
        """
        Called at registration only
        Checks email domain name deliverability
        To prevent false email to register
        """
        validator_args = self.app.config["SECURITY_EMAIL_VALIDATOR_ARGS"] or {}
        if validation_args:
            validator_args.update(validation_args)
        valid = email_validator.validate_email(email, **validator_args)
        return valid.email
