from .base import BaseSiteAdapter

class DefaultSiteAdapter(BaseSiteAdapter):
    """Default adapter that provides generic behavior for any site."""
    
    def __init__(self):
        super().__init__()
        self.domains = set()  # Match any domain
    
    def can_handle(self, url: str) -> bool:
        """Any URL can be handled by the default adapter."""
        return True
