
from flask_mail import Message as _Message
from email.utils import make_msgid

class Message(_Message):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # RFC 2822 does not allow over 78 long Message-ID header or it flags as spam.
        # AWS servers generate way too large hostnames.
        # flask_mail has not method to pass the domain argument to make_msgid, so we have to overload the Message class
        self.msgId = make_msgid(domain="data.public.lu") # Improvement: set from a variable in udata.cfg
