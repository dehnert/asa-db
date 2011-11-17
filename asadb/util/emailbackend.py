from django.conf import settings
from django.core.mail.backends import smtp
from django.core.mail.message import sanitize_address

class ForcedRecipientEmailBackend(smtp.EmailBackend):
    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        if settings.EMAIL_FORCED_RECIPIENTS_LABEL not in email_message.to:
            email_message.to.append(settings.EMAIL_FORCED_RECIPIENTS_LABEL)
        from_email = sanitize_address(email_message.from_email, email_message.encoding)
        recipients = settings.EMAIL_FORCED_RECIPIENTS
        try:
            self.connection.sendmail(from_email, recipients,
                    email_message.message().as_string())
        except:
            if not self.fail_silently:
                raise
            return False
        return True
