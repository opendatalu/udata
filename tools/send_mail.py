from flask import Flask
from flask_mail import Mail, Message
from smtplib import SMTPException

app = Flask(__name__)

# Mail server configuration
app.config["MAIL_SERVER"] = "server-relay.mail.etat.lu"  # Replace with your SMTP server
app.config["MAIL_PORT"] = 25  # Replace with your SMTP port
app.config["MAIL_USE_TLS"] = True  # Enable Transport Layer Security
app.config["MAIL_USE_SSL"] = False  # Enable Secure Sockets Layer (alternatively to TLS)
app.config["MAIL_USERNAME"] = None
app.config["MAIL_PASSWORD"] = None
app.config["MAIL_DEFAULT_SENDER"] = "noreply@data.public.lu"  # Default sender address

# Initialize the Mail object
mail = Mail(app)


def send(subject, recipients):
    """
    Send a given email to multiple recipients.

    User prefered language is taken in account.
    To translate the subject in the right language, you should ugettext_lazy
    """
    if not isinstance(recipients, (list, tuple)):
        recipients = [recipients]
    with mail.connect() as conn:
        for recipient in recipients:
            msg = Message(subject, recipients=[recipient])
            msg.body = "The body of the email"
            msg.html = "<b>HTML</b> body"
            try:
                conn.send(msg)
            except SMTPException as e:
                print(f"Error sending email to {recipient}: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Send an email")
    parser.add_argument(
        "--subject",
        type=str,
        help="The subject of the e mail",
        default="Test email",
        required=False
    )
    parser.add_argument("--recipient", type=str, help="The recipient of the email", required=True)
    args = parser.parse_args()

    # Example usage
    with app.app_context():
        send(args.subject, args.recipient)
