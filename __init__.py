# Copyright (c) 2026 MixedSignalLab
# SPDX-License-Identifier: Apache-2.0
# Author: zhang <mixedsignallab@outlook.com>
# Website: https://www.mixedsignallab.com
# See LICENSE for license terms and NOTICE for attribution.

"""Public package interface for the SmartUSBHub library."""

__version__ = "1.3.1"

# Prefer a relative import (source checkout); fall back to absolute (installed
# as a top-level module via py-modules).
try:
    from .smartusbhub import (
        SmartUSBHub,
        SmartUSBHubError,
        PortBusyError,
        PortPermissionError,
        DeviceConnectionError,
        FeatureNotSupportedError,
        FirmwareUpdateRecommendedWarning,
        DeviceAuthenticationError,
        DeviceAuthenticationCommunicationError,
        DeviceAuthenticationRejectedError,
        AuthenticationNotSupportedError,
        AuthenticationTrustError,
        AuthenticationDependencyError,
        PRODUCT_TYPE_TABLE,
        load_trusted_issuers,
        OPERATE_MODE_NORMAL, OPERATE_MODE_INTERLOCK,
    )
except ImportError:
    from smartusbhub import (
        SmartUSBHub,
        SmartUSBHubError,
        PortBusyError,
        PortPermissionError,
        DeviceConnectionError,
        FeatureNotSupportedError,
        FirmwareUpdateRecommendedWarning,
        DeviceAuthenticationError,
        DeviceAuthenticationCommunicationError,
        DeviceAuthenticationRejectedError,
        AuthenticationNotSupportedError,
        AuthenticationTrustError,
        AuthenticationDependencyError,
        PRODUCT_TYPE_TABLE,
        load_trusted_issuers,
        OPERATE_MODE_NORMAL, OPERATE_MODE_INTERLOCK,
    )

__all__ = [
    '__version__',
    'SmartUSBHub',
    'SmartUSBHubError',
    'PortBusyError',
    'PortPermissionError',
    'DeviceConnectionError',
    'FeatureNotSupportedError',
    'FirmwareUpdateRecommendedWarning',
    'DeviceAuthenticationError',
    'DeviceAuthenticationCommunicationError',
    'DeviceAuthenticationRejectedError',
    'AuthenticationNotSupportedError',
    'AuthenticationTrustError',
    'AuthenticationDependencyError',
    'PRODUCT_TYPE_TABLE',
    'load_trusted_issuers',
    'OPERATE_MODE_NORMAL', 'OPERATE_MODE_INTERLOCK',
]
