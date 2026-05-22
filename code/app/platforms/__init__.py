from .whatsapp import handle_whatsapp
from .telegram import handle_telegram
from .messenger import handle_messenger
from .instagram import handle_instagram

__all__ = ["handle_whatsapp", "handle_telegram", "handle_messenger", "handle_instagram"]
