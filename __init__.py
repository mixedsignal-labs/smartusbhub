# SmartUSBHub Python library
# This is a source repository, smartusbhub.py is the main module

# Import all public API from smartusbhub module
# Try relative import first (for development), then absolute import (for installed package)
try:
    from .smartusbhub import (
        SmartUSBHub,
        FLEXCONNECT_MODE_PC,
        FLEXCONNECT_MODE_UDISK1,
        FLEXCONNECT_MODE_UDISK2,
        FLEXCONNECT_MODE_DISCONNECT,
    )
except ImportError:
    # Fallback to absolute import (when package is installed)
    from smartusbhub import (
        SmartUSBHub,
        FLEXCONNECT_MODE_PC,
        FLEXCONNECT_MODE_UDISK1,
        FLEXCONNECT_MODE_UDISK2,
        FLEXCONNECT_MODE_DISCONNECT,
    )

__all__ = [
    'SmartUSBHub',
    'FLEXCONNECT_MODE_PC',
    'FLEXCONNECT_MODE_UDISK1',
    'FLEXCONNECT_MODE_UDISK2',
    'FLEXCONNECT_MODE_DISCONNECT',
]
