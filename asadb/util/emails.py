from django.core.mail import EmailMessage
from django.template import Context, Template
from django.template.loader import get_template

def email_from_template(tmpl, context,
        subject, to=[], cc=[], from_email='asa-db@mit.edu', ):
    tmpl_obj = get_template(tmpl)
    ctx = Context(context)
    body = tmpl_obj.render(ctx)
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to,
        cc=cc,
        bcc=['asa-db-outgoing@mit.edu', ],
    )
    return email
