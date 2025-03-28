import logging
from typing import Dict, List, Type
from .base import BaseSiteAdapter

logger = logging.getLogger(__name__)

class AdapterRegistry:
    """Registry for site adapters."""
    
    _adapters: Dict[str, Type[BaseSiteAdapter]] = {}
    _instances = {}
    
    @classmethod
    def register(cls, name: str, adapter_class: Type[BaseSiteAdapter]) -> None:
        """
        Register a site adapter.
        
        Args:
            name (str): Name of the adapter
            adapter_class (Type[BaseSiteAdapter]): The adapter class
        """
        cls._adapters[name] = adapter_class
        logger.debug(f"Registered adapter: {name}")
        
    @classmethod
    def get_adapter_for_url(cls, url: str) -> BaseSiteAdapter:
        """
        Get the appropriate adapter for a URL.
        
        Args:
            url (str): The URL to find an adapter for
            
        Returns:
            BaseSiteAdapter: The adapter for the URL, or a default adapter if none found
        """
        for name, adapter_class in cls._adapters.items():
            if name not in cls._instances:
                cls._instances[name] = adapter_class()
                
            adapter = cls._instances[name]
            if adapter.can_handle(url):
                logger.debug(f"Using {name} adapter for {url}")
                return adapter
                
        # If no specific adapter is found, return the default adapter
        if 'default' not in cls._instances:
            from .default import DefaultSiteAdapter
            cls._instances['default'] = DefaultSiteAdapter()
            
        logger.debug(f"Using default adapter for {url}")
        return cls._instances['default']
    
    @classmethod
    def list_adapters(cls) -> List[str]:
        """
        List all registered adapters.
        
        Returns:
            List[str]: Names of registered adapters
        """
        return list(cls._adapters.keys())
