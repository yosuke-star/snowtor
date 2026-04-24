import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)


def error_response(request, message, status=403):
    logger.warning(f"[ERROR_RESPONSE] user={request.user} message={message}")
    return render(request, 'error.html', {'message': message}, status=status)
