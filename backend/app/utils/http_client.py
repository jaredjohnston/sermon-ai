"""
Centralized HTTP client utility with proper SSL configuration
Provides consistent, reliable HTTP connectivity across the application
"""

import ssl
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import aiohttp
import certifi

from app.config.settings import settings

logger = logging.getLogger(__name__)


class HTTPClientError(Exception):
    """Base exception for HTTP client errors"""
    pass


class HTTPClient:
    """
    Centralized HTTP client with proper SSL configuration and error handling
    
    Features:
    - Proper SSL certificate validation using certifi
    - Environment-aware SSL configuration  
    - Consistent error handling
    - Connection pooling and timeout management
    - Development-friendly fallback options
    """
    
    def __init__(self):
        self._ssl_context = None
        self._connector = None
    
    def _get_ssl_context(self) -> ssl.SSLContext:
        """Get or create SSL context with proper certificate validation"""
        if self._ssl_context is None:
            try:
                # Create SSL context with proper certificate bundle
                self._ssl_context = ssl.create_default_context(cafile=certifi.where())
                logger.debug(f"SSL context created with certifi bundle: {certifi.where()}")
                
                # Environment-specific SSL configuration
                if settings.ENVIRONMENT == "development":
                    # In development, we still want proper SSL but can be more lenient
                    logger.debug("Development environment - using standard SSL verification")
                else:
                    # Production - strict SSL verification
                    self._ssl_context.check_hostname = True
                    self._ssl_context.verify_mode = ssl.CERT_REQUIRED
                    logger.debug("Production environment - using strict SSL verification")
                    
            except Exception as e:
                logger.warning(f"Failed to create SSL context with certifi: {e}")
                # Fallback to default SSL context
                self._ssl_context = ssl.create_default_context()
                
        return self._ssl_context
    
    def _create_connector(self) -> aiohttp.TCPConnector:
        """Create a new TCP connector with proper SSL configuration"""
        ssl_context = self._get_ssl_context()
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=100,  # Connection pool limit
            limit_per_host=30,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL (5 minutes)
            use_dns_cache=True,
            keepalive_timeout=30,  # Keep connections alive for 30 seconds
            enable_cleanup_closed=True  # Clean up closed connections
        )
        logger.debug("HTTP connector created with SSL configuration")
        return connector
    
    @asynccontextmanager
    async def session(self, 
                     timeout: Optional[aiohttp.ClientTimeout] = None,
                     headers: Optional[Dict[str, str]] = None,
                     **kwargs) -> aiohttp.ClientSession:
        """
        Create HTTP client session with proper configuration
        
        Args:
            timeout: Custom timeout configuration
            headers: Default headers for all requests
            **kwargs: Additional ClientSession parameters
            
        Yields:
            Configured aiohttp.ClientSession
            
        Example:
            async with http_client.session() as session:
                async with session.get(url) as response:
                    data = await response.read()
        """
        
        # Default timeout configuration
        if timeout is None:
            timeout = aiohttp.ClientTimeout(
                total=30,      # Total timeout
                connect=10,    # Connection timeout  
                sock_read=10   # Socket read timeout
            )
        
        # Default headers
        default_headers = {
            'User-Agent': f'{settings.PROJECT_NAME}/{settings.VERSION}'
        }
        if headers:
            default_headers.update(headers)
        
        connector = self._create_connector()
        session = None
        
        try:
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=default_headers,
                **kwargs
            )
            logger.debug("HTTP session created")
            yield session
            
        except Exception as e:
            logger.error(f"HTTP session error: {e}")
            raise HTTPClientError(f"Failed to create HTTP session: {e}") from e
            
        finally:
            if session and not session.closed:
                await session.close()
                logger.debug("HTTP session closed")
            if connector and not connector.closed:
                await connector.close()
                logger.debug("HTTP connector closed")
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Convenience method for GET requests
        
        Args:
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        async with self.session() as session:
            return await session.get(url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Convenience method for POST requests
        
        Args:
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        async with self.session() as session:
            return await session.post(url, **kwargs)
    
    async def download_file(self, url: str, file_path: str, 
                           chunk_size: int = 8192,
                           progress_callback: Optional[callable] = None) -> int:
        """
        Download file from URL to local path with progress tracking
        
        Args:
            url: Download URL
            file_path: Local file path to save to
            chunk_size: Download chunk size in bytes
            progress_callback: Optional callback for progress updates
            
        Returns:
            Total bytes downloaded
            
        Raises:
            HTTPClientError: If download fails
        """
        try:
            total_size = 0
            
            async with self.session() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise HTTPClientError(f"Download failed: HTTP {response.status}")
                    
                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            f.write(chunk)
                            total_size += len(chunk)
                            
                            if progress_callback:
                                progress_callback(total_size)
            
            logger.info(f"Downloaded {total_size} bytes from {url} to {file_path}")
            return total_size
            
        except Exception as e:
            logger.error(f"File download failed for {url}: {e}")
            raise HTTPClientError(f"Download failed: {e}") from e
    
    async def close(self):
        """Close connector and cleanup resources"""
        if self._connector:
            await self._connector.close()
            self._connector = None
            logger.debug("HTTP connector closed")


# Global HTTP client instance
http_client = HTTPClient()


# Convenience functions for backward compatibility
async def create_session(**kwargs) -> aiohttp.ClientSession:
    """
    Create HTTP session with proper SSL configuration
    
    DEPRECATED: Use http_client.session() context manager instead
    """
    logger.warning("create_session() is deprecated, use http_client.session() instead")
    return http_client.session(**kwargs)


async def download_file(url: str, file_path: str, **kwargs) -> int:
    """Download file with proper SSL configuration"""
    return await http_client.download_file(url, file_path, **kwargs)