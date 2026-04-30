"""
W-MAIL-DACP-MILTER — DKIM Selector Loader
Spec: §227 Section 9 (Q9 decision)
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DKIM_KEYS_PATH = os.environ.get('DKIM_KEYS_PATH', '/dkim/keys')
DEFAULT_DOMAIN = os.environ.get('DOMAIN', 'windisites.de')


class SelectorLoader:
    """Auto-detect DKIM selector from mounted volume"""

    def __init__(self, keys_path: Optional[str] = None):
        self.keys_path = Path(keys_path or DKIM_KEYS_PATH)
        self._selector_cache: Optional[str] = None

    def load_selector(self, domain: Optional[str] = None) -> Optional[str]:
        """
        Load DKIM selector for domain.
        Looks for .txt files in /dkim/keys/{domain}/
        Returns selector name (e.g., 'rsa' from 'rsa.txt')
        """
        if self._selector_cache:
            return self._selector_cache

        domain = domain or DEFAULT_DOMAIN
        domain_path = self.keys_path / domain

        if not domain_path.exists():
            logger.warning(f"DKIM keys directory not found: {domain_path}")
            return None

        # Look for .txt files (DKIM public key records)
        txt_files = list(domain_path.glob('*.txt'))

        if not txt_files:
            logger.warning(f"No DKIM key files found in {domain_path}")
            return None

        # Prefer 'rsa.txt' if exists, otherwise take first
        for txt_file in txt_files:
            if txt_file.stem == 'rsa':
                self._selector_cache = 'rsa'
                logger.info(f"Loaded DKIM selector: rsa")
                return 'rsa'

        # Fall back to first found
        selector = txt_files[0].stem
        self._selector_cache = selector
        logger.info(f"Loaded DKIM selector: {selector}")
        return selector

    def is_loaded(self) -> bool:
        """Check if selector has been loaded"""
        return self._selector_cache is not None

    def get_selector(self) -> Optional[str]:
        """Get cached selector (call load_selector first)"""
        return self._selector_cache


# Singleton instance
_loader: Optional[SelectorLoader] = None


def get_loader() -> SelectorLoader:
    """Get or create selector loader singleton"""
    global _loader
    if _loader is None:
        _loader = SelectorLoader()
    return _loader


def load_dkim_selector(domain: Optional[str] = None) -> Optional[str]:
    """Convenience function to load DKIM selector"""
    return get_loader().load_selector(domain)


def get_dkim_selector() -> Optional[str]:
    """Get cached DKIM selector"""
    return get_loader().get_selector()


def is_selector_loaded() -> bool:
    """Check if DKIM selector is loaded"""
    return get_loader().is_loaded()
