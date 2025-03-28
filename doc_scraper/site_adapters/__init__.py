from .base import BaseSiteAdapter
from .registry import AdapterRegistry
from .default import DefaultSiteAdapter
from .snowflake import SnowflakeAdapter

# Register built-in adapters
AdapterRegistry.register('default', DefaultSiteAdapter)
AdapterRegistry.register('snowflake', SnowflakeAdapter)

__all__ = ['BaseSiteAdapter', 'AdapterRegistry']
