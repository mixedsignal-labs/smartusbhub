##
# @file __init__.py
# @brief Public package interface for the SmartUSBHub library.
# @copyright (c) 2026 MixedSignalLab
# @license Apache-2.0
# @author zhang <mixedsignallab@outlook.com>
# @website https://www.mixedsignallab.com
#
# Re-exports the SmartUSBHub driver class, its exception hierarchy and the
# operating-mode constants so callers can `from smartusbhub import ...` directly.

__version__ = "1.2.0"

# Prefer a relative import (source checkout); fall back to absolute (installed
# as a top-level module via py-modules).
try:
    from .smartusbhub import (
        SmartUSBHub,
        SmartUSBHubError,
        PortBusyError,
        DeviceConnectionError,
        FeatureNotSupportedError,
        PRODUCT_TYPE_TABLE,
        OPERATE_MODE_NORMAL, OPERATE_MODE_INTERLOCK,
    )
except ImportError:
    from smartusbhub import (
        SmartUSBHub,
        SmartUSBHubError,
        PortBusyError,
        DeviceConnectionError,
        FeatureNotSupportedError,
        PRODUCT_TYPE_TABLE,
        OPERATE_MODE_NORMAL, OPERATE_MODE_INTERLOCK,
    )

__all__ = [
    '__version__',
    'SmartUSBHub',
    'SmartUSBHubError',
    'PortBusyError',
    'DeviceConnectionError',
    'FeatureNotSupportedError',
    'PRODUCT_TYPE_TABLE',
    'OPERATE_MODE_NORMAL', 'OPERATE_MODE_INTERLOCK',
]
