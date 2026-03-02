TEMPLATES = {
    'billing': (
        'Thank you for reaching out about your billing concern. '
        'I have flagged your account for our billing team and they will '
        'review the charge within 1 to 2 business days. '
        'You will receive a follow-up email with the outcome.'
    ),
    'technical': (
        'Thank you for reporting this issue. '
        'Our technical team has been notified and is investigating. '
        'In the meantime, please try clearing your cache and logging out, '
        'then logging back in. We will update you within 24 hours.'
    ),
    'account': (
        'Thank you for contacting us about your account. '
        'For security reasons, please verify your identity by clicking the '
        'link we will send to your registered email address. '
        'Once verified, our team will assist you within a few hours.'
    ),
    'shipping': (
        'Thank you for your message about your shipment. '
        'I have escalated your order to our fulfillment team for review. '
        'You will receive an update with tracking information or a resolution '
        'within 1 business day.'
    ),
    'general': (
        'Thank you for reaching out. '
        'A member of our team will review your message and get back to you '
        'within 1 business day. '
        'We appreciate your feedback and patience.'
    )
}


def get_reply(category):
    return TEMPLATES.get(category, TEMPLATES['general'])

