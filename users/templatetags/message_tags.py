from django import template
from django.contrib import messages
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def display_messages_with_auto_clear(context):
    """
    Display Django messages with automatic clearing functionality.
    This tag will show messages and the JavaScript MessageManager will handle removal.
    """
    if not messages.get_messages(context["request"]):
        return ""

    message_html = []
    message_html.append('<div id="django-messages" class="messages-container">')

    for message in messages.get_messages(context["request"]):
        css_class = "alert"
        if message.tags:
            if message.tags == "error":
                css_class += " alert-danger"
            elif message.tags == "warning":
                css_class += " alert-warning"
            elif message.tags == "success":
                css_class += " alert-success"
            elif message.tags == "info":
                css_class += " alert-info"

        message_html.append(
            f'<div class="{css_class} alert-dismissible fade show" role="alert" data-message-id="{id(message)}">'
        )
        message_html.append(f"<span>{message}</span>")
        message_html.append(
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>'
        )
        message_html.append("</div>")

    message_html.append("</div>")

    return mark_safe("".join(message_html))


@register.simple_tag(takes_context=True)
def clear_messages(context):
    """
    Clear all Django messages from the session.
    This can be used to manually clear messages if needed.
    """
    if hasattr(context["request"], "_messages"):
        context["request"]._messages._queued_messages = []
    return ""
