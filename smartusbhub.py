"""
High-level driver for controlling a Smart USB Hub over a UART serial link.

Project website: https://www.mixedsignallab.com

The SmartUSBHub class provides robust per-port control of power and data
connections, voltage/current monitoring, configuration of default states,
and factory reset. It is intended for automated test systems and hardware
development workflows.

**Wire protocol**

Three framing variants share the same serial channel; frames are
distinguished by their start-of-frame (SOF) bytes:

- **V1** (6 bytes): ``0x55`` ``0x5A`` ``CMD`` ``CHANNEL`` ``VALUE`` ``CHECKSUM``,
  where ``CHECKSUM`` = (CMD + CHANNEL + VALUE) & 0xFF. Used for most set/get
  commands. ``CHANNEL`` is a bitmask (bit0 = channel 1, bit1 = channel 2, ...).
- **V2** (7 bytes): ``0x55`` ``0x5A`` ``CMD`` ``CHANNEL`` ``VALUE0`` ``VALUE1``
  ``CHECKSUM``. Used for 16-bit payloads (voltage/current) and for the
  enable/value pairs of the default power/dataline commands.
- **V3** (>=10 bytes): ``0x55`` ``0xAB`` ``0xCD`` ``0xEF`` SOF magic, followed by
  ``CMD``, ``FLAGS``, a little-endian 16-bit ``LENGTH``, a little-endian 16-bit
  CRC16 (poly 0x8005, init 0xFFFF, computed with the CRC field zeroed), and a
  variable-length payload. Used for batch measurements and measurement
  streaming. Frames whose ``FLAGS`` carry ``V3_FLAG_STREAM`` are unsolicited
  notifications and are not acknowledged by the host.

Refer to the product documentation shipped with your release package for the
authoritative command reference.
"""

import os
import time
import atexit
import logging
import weakref
import tempfile
import threading
from functools import wraps

import serial
import serial.tools.list_ports

__version__ = "1.2.0"

# Cross-process file lock support: prefer fcntl (Unix/Linux/macOS), fall back to
# msvcrt (Windows). When neither is available, port locking degrades to a
# process-local check only. Both flags are always defined so either may be
# tested unconditionally.
HAS_FCNTL = False
HAS_MSVCRT = False
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    try:
        import msvcrt
        HAS_MSVCRT = True
    except ImportError:
        pass
class SmartUSBHubError(Exception):
    """
    Base class for all errors raised by this library.

    Catch this to handle any SmartUSBHub-specific failure regardless of subtype.
    """
    pass

class PortBusyError(SmartUSBHubError, ValueError):
    """
    Raised when a serial port is already in use by another instance or process.

    Also subclasses ``ValueError`` for backward compatibility with callers that
    previously caught the ``ValueError`` raised on a busy port.
    """
    pass

class DeviceConnectionError(SmartUSBHubError):
    """
    Raised when a device does not respond during connection setup.

    Typically means the port is not a SmartUSBHub or the device is unresponsive.
    """
    pass

class FeatureNotSupportedError(SmartUSBHubError, ValueError):
    """
    Raised when a requested feature is not supported by the connected product model.

    Also subclasses ``ValueError`` for backward compatibility.
    """
    pass


# --- Command codes -----------------------------------------------------------
CMD_GET_CHANNEL_POWER_STATUS        = 0x00  # query channel VBUS power state
CMD_SET_CHANNEL_POWER               = 0x01  # set channel VBUS power state
CMD_SET_CHANNEL_POWER_INTERLOCK     = 0x02  # select one powered channel, or clear interlock
CMD_GET_CHANNEL_VOLTAGE             = 0x03  # query one channel voltage sample
CMD_GET_CHANNEL_CURRENT             = 0x04  # query one channel current sample
CMD_SET_CHANNEL_DATALINE            = 0x05  # set USB2 D+/D- data-line switch state
CMD_GET_CHANNEL_DATALINE_STATUS     = 0x08  # query USB2 D+/D- data-line switch state

CMD_SET_BUTTON_CONTROL              = 0x09  # enable or disable front-panel button control
CMD_GET_BUTTON_CONTROL_STATUS       = 0x0A  # query front-panel button-control state

CMD_SET_DEFAULT_POWER_STATUS        = 0x0B  # set boot/default VBUS power state
CMD_GET_DEFAULT_POWER_STATUS        = 0x0C  # query boot/default VBUS power state
CMD_SET_DEFAULT_DATALINE_STATUS     = 0x0D  # set boot/default USB2 data-line state
CMD_GET_DEFAULT_DATALINE_STATUS     = 0x0E  # query boot/default USB2 data-line state

CMD_SET_AUTO_RESTORE                = 0x0F  # enable or disable power-loss auto-restore
CMD_GET_AUTO_RESTORE_STATUS         = 0x10  # query power-loss auto-restore state

CMD_SET_OPERATE_MODE                = 0x06  # set device operating mode
CMD_GET_OPERATE_MODE                = 0x07  # query device operating mode

CMD_SET_DEVICE_ADDRESS              = 0x11  # set multi-hub device address
CMD_GET_DEVICE_ADDRESS              = 0x12  # query multi-hub device address

CMD_GET_CHANNEL_MEASUREMENTS        = 0x1A  # V3 query/stream: voltage/current samples
CMD_GET_CHANNEL_OC_STATUS           = 0x1B  # query/unsolicited: channel=active_mask, value=latch_mask
CMD_CLEAR_CHANNEL_OC_LATCH          = 0x1C  # clear the sticky OC latch for a channel mask
CMD_IDENTIFY_DEVICE                 = 0x1D  # quick blink status LED to locate device
CMD_SET_CHANNEL_NAME                = 0x1E  # V3 payload: [channel(1-based), utf8 name]
CMD_GET_CHANNEL_NAME                = 0x1F  # V3 payload: request/response [channel(1-based), utf8 name]
CMD_SET_DEVICE_ALIAS                = 0x20  # V3 payload: utf8 alias
CMD_GET_DEVICE_ALIAS                = 0x21  # V3 payload response: utf8 alias
CMD_REBOOT_MCU                      = 0xF7  # reboot the device MCU
CMD_GET_SERIAL_NO                   = 0xF9  # query device serial number
CMD_GET_PRODUCT_TYPE                = 0xF0  # query product-type code
CMD_GET_MAX_CHANNELS                = 0xF1  # query maximum supported channel count
CMD_FACTORY_RESET                   = 0xFC  # restore persistent settings to factory defaults
CMD_GET_FIRMWARE_VERSION            = 0xFD  # query firmware version
CMD_GET_HARDWARE_VERSION            = 0xFE  # query hardware version

# --- V3 framing constants ----------------------------------------------------
V3_MAGIC                            = (0x55, 0xAB, 0xCD, 0xEF)  # 4-byte SOF magic
V3_HEADER_LEN                       = 10   # 4 SOF + cmd + flags + length(2) + crc(2)
V3_MAX_FRAME_LEN                    = 64
V3_MAX_DATA_LEN                     = V3_MAX_FRAME_LEN - V3_HEADER_LEN
V3_FLAG_STREAM                      = 0x01
V3_MEAS_FLAG_FORCE_SAMPLE           = 0x01
V3_MEAS_FLAG_STREAM_ENABLE          = 0x02
V3_MEAS_FLAG_STREAM_DISABLE         = 0x04
V3_STATUS_OK                        = 0x00

# --- Operating modes ---------------------------------------------------------
# Channels are addressed by 1-based number throughout the public API (e.g.
# set_channel_power(1, 2, state=1)); the wire-level bitmask is derived
# internally, so no per-channel constants are exposed.
OPERATE_MODE_NORMAL = 0
OPERATE_MODE_INTERLOCK = 1

# Product capability table keyed by product-type ID.
#
# Each entry describes hardware capabilities. A True value does not by itself
# guarantee that this SDK version exposes a public control method for that
# capability (USB3/ILIM are currently metadata-only):
# - ``name``: short product identifier
# - ``channels``: number of channels
# - ``description``: human-readable description
# - ``enable_adc``: voltage/current monitoring supported
# - ``enable_usb2_data_switch``: USB2.0 data-line switching supported
# - ``enable_usb3_data_switch``: USB3.0 data-line switching supported
# - ``enable_ilim_switch``: current-limit / slow-fast charge switching supported
# - ``ack_timeout``: per-command ACK timeout in seconds
PRODUCT_TYPE_TABLE = {
    0x00: {
        "name": "HBP_USB2_4CH",
        "channels": 4,
        "description": "USB2.0 4-channel hub",
        "enable_adc": True,
        "enable_usb2_data_switch": True,
        "enable_usb3_data_switch": False,
        "enable_ilim_switch": False,
        "ack_timeout": 0.1,
    },
    0x01: {
        "name": "HBP_USB2_2CH",
        "channels": 2,
        "description": "USB2.0 2-channel hub",
        "enable_adc": False,
        "enable_usb2_data_switch": False,
        "enable_usb3_data_switch": False,
        "enable_ilim_switch": False,
        "ack_timeout": 0.1,
    },
    0x02: {
        "name": "HBP_USB2_7CH",
        "channels": 7,
        "description": "USB2.0 7-channel hub",
        "enable_adc": True,
        "enable_usb2_data_switch": True,
        "enable_usb3_data_switch": False,
        "enable_ilim_switch": False,
        "ack_timeout": 0.1,
    },
    0x03: {
        "name": "HBP_USB2_7CH_ADV",
        "channels": 7,
        "description": "USB2.0 7-channel hub with INA3221 voltage/current monitoring",
        "enable_adc": True,
        "enable_usb2_data_switch": True,
        "enable_usb3_data_switch": False,
        "enable_ilim_switch": False,
        "ack_timeout": 0.1,
    },
    0x04: {
        "name": "HBP_USB3_4CH",
        "channels": 4,
        "description": "USB3.0 4-channel hub",
        "enable_adc": False,
        "enable_usb2_data_switch": True,
        "enable_usb3_data_switch": True,
        "enable_ilim_switch": True,
        "ack_timeout": 0.1,
    },
    0x05: {
        "name": "HBL_USB2_4CH",
        "channels": 4,
        "description": "USB2.0 4-channel power-control hub with overcurrent reporting",
        "enable_adc": False,
        "enable_usb2_data_switch": False,
        "enable_usb3_data_switch": False,
        "enable_ilim_switch": False,
        "enable_overcurrent": True,
        "ack_timeout": 0.1,
    },
}

# Library logging follows the standard practice of attaching only a NullHandler;
# the consuming application is responsible for configuring handlers and levels.
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# When False, the synchronized decorator becomes a no-op.
#
# Intended for tests that need to exercise behaviour without the per-instance
# command lock. Leave True in production.
ENABLE_SYNC_LOCK = True


def synchronized(method):
    """
    Decorator that serializes access to a SmartUSBHub method via the instance lock.

    When ``ENABLE_SYNC_LOCK`` is True the wrapped method acquires ``self.lock`` for
    its whole duration; when False it runs without locking.

    :param method: The instance method to wrap.

    :returns: The wrapped method.
    """

    @wraps(method)
    def _synchronized(self, *args, **kwargs):
        if ENABLE_SYNC_LOCK:
            with self.lock:
                return method(self, *args, **kwargs)
        return method(self, *args, **kwargs)
    return _synchronized


class _Codec:
    """
    Pure wire-protocol codec for the SmartUSBHub serial link (no I/O, no state).

    All framing knowledge — the V1/V2/V3 layouts, the CRC16, the V1 checksum and
    the per-command V1-vs-V2 sizing — lives here in one place, so the send path,
    the receive loop's frame-sizing and the parser can never disagree. Every method
    is a pure function of its arguments and is unit-testable without a device.
    """

    # Reply frames that use the 7-byte V2 framing (two payload bytes); every other
    # V1/V2 reply uses the 6-byte V1 framing. This is the per-command sizing table
    # the parser and the receive loop both consult.
    V2_REPLY_COMMANDS = (
        CMD_GET_CHANNEL_VOLTAGE, CMD_GET_CHANNEL_CURRENT,
        CMD_SET_DEFAULT_POWER_STATUS, CMD_SET_DEFAULT_DATALINE_STATUS,
        CMD_GET_DEFAULT_POWER_STATUS, CMD_GET_DEFAULT_DATALINE_STATUS,
    )

    @staticmethod
    def crc16(data):
        """Compute a CRC16 over ``data`` (poly 0x8005, init 0xFFFF), used by V3."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0x8005
                else:
                    crc = crc >> 1
        return crc & 0xFFFF

    @staticmethod
    def encode_v1v2(cmd, channel_mask, data):
        """
        Build a V1/V2 frame ``55 5A | cmd | mask | data... | checksum``.

        :param cmd: Command byte.

        :param channel_mask: Channel-mask byte (the caller derives it).

        :param data: Iterable of payload bytes following the mask.

        :returns: The frame bytearray.
        """
        payload = [channel_mask] + list(data)
        packet = bytearray([0x55, 0x5A, cmd])
        packet.extend(payload)
        packet.append((cmd + sum(payload)) & 0xFF)
        return packet

    @staticmethod
    def encode_v3(cmd, payload=b""):
        """
        Build a V3 frame ``55 AB CD EF | cmd | flags | len(2) | crc16(2) | payload``.

        Accepts payload as bytes, bytearray, list of ints, or a single int.

        :param cmd: Command byte.

        :param payload: Payload bytes (or list/int).

        :returns: The frame bytearray.

        :raises ValueError: If the payload exceeds ``V3_MAX_DATA_LEN.``
        """
        if payload is None:
            payload = b""
        elif isinstance(payload, list):
            payload = bytes(payload)
        elif not isinstance(payload, (bytes, bytearray)):
            payload = bytes([payload])
        payload = bytes(payload)

        if len(payload) > V3_MAX_DATA_LEN:
            raise ValueError(f"V3 payload too large: {len(payload)} > {V3_MAX_DATA_LEN}")

        # Header: [0-3] SOF magic, [4] cmd, [5] flags, [6-7] length, [8-9] crc16.
        packet = bytearray([
            0x55, 0xAB, 0xCD, 0xEF,
            cmd & 0xFF,
            0x00,
            len(payload) & 0xFF,
            (len(payload) >> 8) & 0xFF,
            0x00, 0x00,
        ]) + payload
        crc = _Codec.crc16(packet)
        packet[8] = crc & 0xFF
        packet[9] = (crc >> 8) & 0xFF
        return packet

    @staticmethod
    def parse_frame(data):
        """
        Parse one frame from the front of ``data`` (V1/V2/V3).

        :param data: Raw bytes received from the device.

        :returns: Tuple (cmd, channel, value, length) on success, else None when the
            buffer holds only a partial frame or the frame is invalid. For V3 frames,
            channel is 0 and value is a dict {"v3", "stream", "payload"}.
        """
        if len(data) < 6:
            return None

        # V3 protocol: 4-byte SOF magic 0x55 0xAB 0xCD 0xEF.
        if data[0] == 0x55 and data[1] == 0xAB:
            if len(data) < V3_HEADER_LEN:
                return None
            if data[2] != 0xCD or data[3] != 0xEF:
                logger.debug(f"V3 magic mismatch: {data[2]:02X} {data[3]:02X}")
                return None

            # Header: [0-3] magic, [4] cmd, [5] flags, [6-7] length, [8-9] crc16.
            cmd = data[4]
            flags = data[5]
            data_length = data[6] | (data[7] << 8)
            if data_length > V3_MAX_DATA_LEN:
                logger.debug(f"Invalid V3 payload length: {data_length} > {V3_MAX_DATA_LEN}")
                return None
            received_crc16 = data[8] | (data[9] << 8)

            total_length = V3_HEADER_LEN + data_length
            if len(data) < total_length:
                return None

            crc_data = bytearray(data[:total_length])
            crc_data[8] = 0   # zero the CRC field before verification
            crc_data[9] = 0
            calculated_crc16 = _Codec.crc16(crc_data)
            if calculated_crc16 != received_crc16:
                logger.debug(f"Invalid V3 CRC16: calculated={calculated_crc16:04X}, "
                             f"received={received_crc16:04X}")
                return None

            data_value = {
                "v3": True,
                "stream": bool(flags & V3_FLAG_STREAM),
                "payload": bytes(data[V3_HEADER_LEN:total_length]),
            }
            logger.debug(f"Received V3 frame: cmd={cmd:04X}, length={data_length}")
            return (cmd, 0, data_value, total_length)

        # V1/V2 protocol: SOF 0x55 0x5A.
        if data[0] != 0x55 or data[1] != 0x5A:
            return None

        cmd = data[2]
        channel = data[3]

        if cmd in _Codec.V2_REPLY_COMMANDS:
            # V2 frame: two payload bytes.
            if len(data) < 7:
                return None
            value_0 = data[4]
            value_1 = data[5]
            checksum = data[6]
            if (cmd + channel + value_0 + value_1) & 0xFF != checksum:
                logger.debug(f"Invalid V2 checksum for channel {channel}")
                return None
            return (cmd, channel, [value_0, value_1], 7)

        # V1 frame: single payload byte.
        value = data[4]
        checksum = data[5]
        if (cmd + channel + value) & 0xFF != checksum:
            return None
        return (cmd, channel, value, 6)


class _PortLock:
    """
    Cross-process exclusive lock for a serial port, backed by an OS file lock.

    Uses ``fcntl`` on Unix/macOS and ``msvcrt`` on Windows; where neither exists the
    lock degrades to success (the caller's in-process port registry still prevents
    double-open within one process). A lock file left behind by a dead process is
    detected via its recorded PID and reaped, so a crashed owner never wedges a port
    permanently. State and behaviour are identical to the former ``SmartUSBHub``
    classmethods; this just isolates the OS-specific locking in one testable unit.
    """

    _locks = {}        # {port: open lock-file handle}
    _lock_dir = None   # lock-file directory (lazily created)

    @classmethod
    def _get_lock_dir(cls):
        """
        Return the directory used to store per-port lock files, creating it if needed.

        :returns: Absolute path to the lock-file directory.
        """
        if cls._lock_dir is None:
            cls._lock_dir = os.path.join(tempfile.gettempdir(), 'smartusbhub_locks')
            os.makedirs(cls._lock_dir, exist_ok=True)
        return cls._lock_dir

    @classmethod
    def _check_process_exists(cls, pid):
        """
        Check whether a process with the given PID currently exists.

        :param pid: Process ID to probe.

        :returns: True if the process exists, False otherwise.
        """
        try:
            if os.name == 'nt':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_INFORMATION
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            os.kill(pid, 0)  # signal 0 only probes for existence
            return True
        except (OSError, ProcessLookupError, AttributeError):
            return False

    @classmethod
    def _clear_stale_lock(cls, lock_file_path):
        """
        Remove a lock file if it is owned by a process that no longer exists.

        :param lock_file_path: Path to the candidate lock file.
        """
        if not os.path.exists(lock_file_path):
            return
        try:
            with open(lock_file_path, 'r') as f:
                pid_str = f.read().strip()
            if pid_str.isdigit() and not cls._check_process_exists(int(pid_str)):
                logger.debug(f"Removing stale lock file {lock_file_path}")
                os.remove(lock_file_path)
        except Exception as e:
            logger.debug(f"Error inspecting lock file {lock_file_path}: {e}")

    @classmethod
    def acquire(cls, port):
        """
        Acquire a non-blocking cross-process file lock for a serial port.

        Stale lock files left behind by dead processes are detected and removed.
        On platforms without file-locking support this degrades to success.

        :param port: Serial port name.

        :returns: True if the lock was acquired (or locking is unsupported), else False.
        """
        if port in cls._locks:
            return True

        safe_port_name = port.replace('/', '_').replace('\\', '_').replace(':', '_')
        lock_file_path = os.path.join(cls._get_lock_dir(), f'{safe_port_name}.lock')

        if not HAS_FCNTL and not HAS_MSVCRT:
            logger.warning("File locking is unsupported on this platform; "
                           "falling back to a process-local check only.")
            return True

        for attempt in (0, 1):
            # On the second attempt the lock file has just been cleared as stale.
            try:
                lock_file = open(lock_file_path, 'a+')
                try:
                    if HAS_FCNTL:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    else:
                        lock_file.seek(0)
                        if os.path.getsize(lock_file_path) == 0:
                            lock_file.write('0')
                            lock_file.flush()
                        lock_file.seek(0)
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                except (IOError, OSError):
                    lock_file.close()
                    if attempt == 0:
                        cls._clear_stale_lock(lock_file_path)
                        continue
                    logger.warning(f"Port {port} is locked by another process")
                    return False

                cls._locks[port] = lock_file
                lock_file.seek(0)
                lock_file.truncate()
                lock_file.write(str(os.getpid()))
                lock_file.flush()
                logger.debug(f"Acquired file lock for port {port}")
                return True
            except Exception as e:
                logger.error(f"Failed to acquire lock for port {port}: {e}")
                return False
        return False

    @classmethod
    def release(cls, port):
        """
        Release the cross-process file lock held for a serial port.

        :param port: Serial port name.
        """
        lock_file = cls._locks.pop(port, None)
        if lock_file is None:
            return
        try:
            if HAS_FCNTL:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            elif HAS_MSVCRT:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            lock_file.close()
            logger.debug(f"Released file lock for port {port}")
        except Exception as e:
            logger.error(f"Failed to release lock for port {port}: {e}")


class SmartUSBHub:
    """
    High-level interface to an industrial Smart USB Hub over UART.

    Provides per-port control of power and data connections, voltage/current
    monitoring, default-state configuration and factory reset. Suitable for
    automated test systems and hardware development.

    Instances may be used as context managers; the device is disconnected on exit:

    .. code-block:: python

       with SmartUSBHub(port) as hub:
       hub.set_channel_power(1, state=1)
    """

    # Process-local registry of open ports and their device addresses. Used to
    # detect double-open within a process; the cross-process file lock lives in
    # ``_PortLock``.
    _connected_ports = set()
    _connected_addresses = {}        # {port: address}
    _instances = weakref.WeakSet()   # live instances, for atexit cleanup

    @classmethod
    def _acquire_port_lock(cls, port):
        """Acquire the cross-process lock for ``port``. See ``_PortLock.acquire``."""
        return _PortLock.acquire(port)

    @classmethod
    def _release_port_lock(cls, port):
        """Release the cross-process lock for ``port``. See ``_PortLock.release``."""
        return _PortLock.release(port)

    @classmethod
    def _cleanup_all_instances(cls):
        """Disconnect every live instance. Registered with atexit for safe shutdown."""
        for instance in list(cls._instances):
            try:
                instance.disconnect()
            except Exception:
                pass

    # Commands that the device acknowledges and that the host may wait on.
    _ACK_COMMANDS = (
        CMD_GET_OPERATE_MODE, CMD_SET_OPERATE_MODE,
        CMD_SET_CHANNEL_POWER, CMD_GET_CHANNEL_POWER_STATUS,
        CMD_SET_CHANNEL_POWER_INTERLOCK,
        CMD_GET_CHANNEL_VOLTAGE, CMD_GET_CHANNEL_CURRENT,
        CMD_GET_CHANNEL_MEASUREMENTS,
        CMD_GET_CHANNEL_OC_STATUS, CMD_CLEAR_CHANNEL_OC_LATCH,
        CMD_IDENTIFY_DEVICE,
        CMD_SET_CHANNEL_NAME, CMD_GET_CHANNEL_NAME,
        CMD_SET_DEVICE_ALIAS, CMD_GET_DEVICE_ALIAS,
        CMD_SET_CHANNEL_DATALINE, CMD_GET_CHANNEL_DATALINE_STATUS,
        CMD_SET_BUTTON_CONTROL, CMD_GET_BUTTON_CONTROL_STATUS,
        CMD_SET_DEFAULT_POWER_STATUS, CMD_GET_DEFAULT_POWER_STATUS,
        CMD_SET_DEFAULT_DATALINE_STATUS, CMD_GET_DEFAULT_DATALINE_STATUS,
        CMD_SET_AUTO_RESTORE, CMD_GET_AUTO_RESTORE_STATUS,
        CMD_SET_DEVICE_ADDRESS, CMD_GET_DEVICE_ADDRESS,
        CMD_REBOOT_MCU, CMD_GET_PRODUCT_TYPE, CMD_GET_MAX_CHANNELS,
        CMD_GET_SERIAL_NO, CMD_FACTORY_RESET,
        CMD_GET_FIRMWARE_VERSION, CMD_GET_HARDWARE_VERSION,
    )

    # Wire framing tables live on the codec; alias here so the receive loop's
    # frame-sizing (``self._V2_REPLY_COMMANDS``) reads the same single source.
    _V2_REPLY_COMMANDS = _Codec.V2_REPLY_COMMANDS

    def __init__(self, port):
        """
        Open a Smart USB Hub on the given serial port and read its identity.

        Acquires a process-local and cross-process lock on the port, opens the
        serial link at 115200 baud, starts the background receive thread and
        queries device information. The constructor blocks until the device
        identity is read or the attempt times out.

        :param port: Serial port name (e.g. "/dev/ttyUSB0" or "COM3").

        :raises PortBusyError: If the port is already in use by another instance or process.

        :raises DeviceConnectionError: If the device does not respond during setup.

        :raises serial.SerialException: For other serial-layer failures.
        """
        self.port = port
        self.name = f"smarthub_id:{port.split('/')[-1]}"

        if port in SmartUSBHub._connected_ports:
            raise PortBusyError(
                f"Port {port} is already in use by another SmartUSBHub instance. "
                f"Disconnect the existing instance first or use a different port.")

        if not self._acquire_port_lock(port):
            raise PortBusyError(
                f"Port {port} is already in use by another process. "
                f"Disconnect the existing connection first or use a different port.")

        try:
            self.ser = serial.Serial(port, 115200, timeout=0.5)
            SmartUSBHub._connected_ports.add(port)
            SmartUSBHub._instances.add(self)
        except serial.SerialException as e:
            self._release_port_lock(port)
            msg = str(e).lower()
            if "could not open port" in msg or "access is denied" in msg:
                raise PortBusyError(
                    f"Port {port} is already in use. Disconnect the existing connection first.")
            raise

        # Default ACK timeout; refined per product model once the type is known.
        self.com_timeout = 0.1
        logger.info(f"SmartUSBHub initialized on port {self.port}")

        # One ACK Event per command; the receive thread sets it when a matching
        # frame arrives and the calling thread waits on it.
        self.ack_events = {cmd: threading.Event() for cmd in self._ACK_COMMANDS}
        self.callbacks = {cmd: None for cmd in self.ack_events}

        # Maps an incoming command code to the handler that updates cached state.
        self._frame_handlers = {
            CMD_SET_CHANNEL_POWER: self._handle_set_channel_power_status,
            CMD_GET_CHANNEL_POWER_STATUS: self._handle_get_channel_power_status,
            CMD_SET_CHANNEL_POWER_INTERLOCK: self._handle_power_interlock_control,
            CMD_GET_CHANNEL_OC_STATUS: self._handle_oc_status,
            CMD_CLEAR_CHANNEL_OC_LATCH: self._handle_oc_status,
            CMD_GET_CHANNEL_VOLTAGE: self._handle_get_channel_voltage,
            CMD_GET_CHANNEL_CURRENT: self._handle_get_channel_current,
            CMD_GET_CHANNEL_MEASUREMENTS: self._handle_get_channel_measurements,
            CMD_SET_CHANNEL_DATALINE: self._handle_set_channel_dataline,
            CMD_IDENTIFY_DEVICE: self._handle_identify_device,
            CMD_SET_CHANNEL_NAME: self._handle_channel_name,
            CMD_GET_CHANNEL_NAME: self._handle_channel_name,
            CMD_SET_DEVICE_ALIAS: self._handle_device_alias,
            CMD_GET_DEVICE_ALIAS: self._handle_device_alias,
            CMD_GET_CHANNEL_DATALINE_STATUS: self._handle_get_channel_dataline,
            CMD_SET_BUTTON_CONTROL: self._handle_set_button_control,
            CMD_GET_BUTTON_CONTROL_STATUS: self._handle_get_button_control,
            CMD_SET_DEFAULT_POWER_STATUS: self._handle_set_default_power_status,
            CMD_GET_DEFAULT_POWER_STATUS: self._handle_get_default_power_status,
            CMD_SET_DEFAULT_DATALINE_STATUS: self._handle_set_default_dataline_status,
            CMD_GET_DEFAULT_DATALINE_STATUS: self._handle_get_default_dataline_status,
            CMD_SET_AUTO_RESTORE: self._handle_set_auto_restore,
            CMD_GET_AUTO_RESTORE_STATUS: self._handle_get_auto_restore_status,
            CMD_GET_OPERATE_MODE: self._handle_get_operate_mode,
            CMD_SET_OPERATE_MODE: self._handle_set_operate_mode,
            CMD_SET_DEVICE_ADDRESS: self._handle_set_device_address,
            CMD_GET_DEVICE_ADDRESS: self._handle_get_device_address,
            CMD_REBOOT_MCU: self._handle_reboot_mcu,
            CMD_FACTORY_RESET: self._handle_factory_reset,
            CMD_GET_FIRMWARE_VERSION: self._handle_firmware_version,
            CMD_GET_HARDWARE_VERSION: self._handle_hardware_version,
            CMD_GET_PRODUCT_TYPE: self._handle_product_type,
            CMD_GET_MAX_CHANNELS: self._handle_get_max_channels,
            CMD_GET_SERIAL_NO: self._handle_serial_no,
        }

        self.lock = threading.Lock()        # serializes @synchronized methods
        self._send_lock = threading.Lock()  # serializes raw serial writes

        # Command pacing. These defaults were tuned on hardware to sit just above
        # the physical USB-CDC + MCU round-trip floor (~2.5 ms/command): a 10000-
        # command sustained run held 100% with these values. Raise them only if a
        # flakier link (long cable / passive hub) drops ACKs; lowering further
        # yields nothing (the device is already the limit) and rx poll must stay
        # >0 so the receive thread does not busy-spin a CPU core.
        self._last_send_time = 0
        self._min_send_interval = 0.001   # >= 1 ms between writes (burst guard)
        self._mcu_response_wait = 0.000   # no settle; the reply is awaited explicitly
        # How often the receive thread polls the serial port for reply bytes.
        # Bounds reply-detection latency; lowering it makes commands feel snappier
        # at the cost of more CPU wakeups (no effect on the MCU).
        self._rx_poll_interval = 0.001

        self.disconnect_callback = None

        # Cached device identity / configuration.
        self.hardware_version = None
        self.firmware_version = None
        self.firmware_version_major = None
        self.firmware_version_minor = None
        self.product_type = None
        self.max_channels = None
        self.serial_no = None
        self.operate_mode = None
        self.auto_restore_status = None
        self.button_control_status = None
        self.device_address = None
        self.device_alias = ""

        # Cached per-channel state, keyed by 1-based channel number.
        self.channel_default_power_flag = {}
        self.channel_default_power_status = {}
        self.channel_names = {}
        self.channel_default_dataline_flag = {}
        self.channel_default_dataline_status = {}
        self.channel_power_status = {}
        self.channel_dataline_status = {}
        self.channel_oc_active = {}   # {ch: bool} current FLAG# state
        self.channel_oc_latch = {}    # {ch: bool} sticky latch, cleared by command
        self.channel_voltages = {}
        self.channel_currents = {}
        self.channel_measurement_fresh = {}
        self.channel_measurement_valid = {}
        self.channel_measurement_sample_tick = {}

        # Signalled by the receive thread after every dispatched frame, so a
        # caller can wait for content-based completion (e.g. a multi-channel read
        # collecting one reply frame per channel) instead of a fixed settle delay.
        self._frame_condition = threading.Condition()

        # V3 measurement-stream bookkeeping.
        self._measurement_stream_condition = threading.Condition()
        self._measurement_stream_seq = 0
        self._measurement_stream_tick = None
        self._measurement_stream_period_ms = None
        self._last_v3_status = {}

        # Consecutive ACK failures before an MCU recovery is attempted.
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5

        try:
            self._start()
            # Allow the MCU state machine to settle if it was previously stuck
            # (stuck detection is 100 ms, timeout detection 20 ms).
            time.sleep(0.15)
            self.get_device_info()

            if self.operate_mode is None:
                logger.error("Failed to read operate mode; device is not responding.")
                raise DeviceConnectionError(
                    f"Device on port {self.port} did not respond to the operate-mode query. "
                    f"The port may not be a SmartUSBHub, or the device is unresponsive.")

            if self.device_address is not None:
                SmartUSBHub._connected_addresses[port] = self.device_address

            logger.info(f"Hardware version: V1.{self.hardware_version}")
            logger.info(f"Firmware version: {self.get_firmware_version_string()}")
            logger.info(f"Operate mode: {'normal' if self.operate_mode == 0 else 'interlock'}")
            logger.info(f"Button control: {'enabled' if self.button_control_status == 1 else 'disabled'}")
        except Exception:
            self.disconnect()
            raise

    def __enter__(self):
        """
        Enter the runtime context and return this instance.

        :returns: self
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the runtime context, disconnecting the device.

        :returns: False (exceptions are never suppressed).
        """
        self.disconnect()
        return False

    def close(self):
        """Close the connection. Alias for ``disconnect.``"""
        self.disconnect()

    def register_disconnect_callback(self, callback):
        """
        Register a callback invoked when the device disconnects unexpectedly.

        :param callback: Zero-argument callable executed on disconnect.
        """
        self.disconnect_callback = callback

    def register_callback(self, cmd, callback):
        """
        Register a callback invoked when a command's ACK is received.

        :param cmd: Command code to attach the callback to.

        :param callback: Callable receiving (channel, value) when the ACK arrives.
        """
        if cmd in self.callbacks:
            self.callbacks[cmd] = callback
            logger.info(f"Callback registered for command {cmd:#04x}")
        else:
            logger.warning(f"Invalid command {cmd:#04x}; cannot register callback.")

    def _invoke_callback(self, cmd, *args, **kwargs):
        """
        Invoke the user callback registered for a command, if any.

        :param cmd: Command code whose callback should run.

        :param args: Positional arguments forwarded to the callback.

        :param kwargs: Keyword arguments forwarded to the callback.
        """
        callback = self.callbacks.get(cmd)
        if callback:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in callback for command {cmd:#04x}: {e}")

    @staticmethod
    def get_product_info(product_type_id):
        """
        Look up the capability record for a product-type ID.

        :param product_type_id: Product-type ID (see ``PRODUCT_TYPE_TABLE``).

        :returns: The product-info dict, or None if the ID is unknown.
        """
        return PRODUCT_TYPE_TABLE.get(product_type_id)

    def _check_feature_support(self, feature_name):
        """
        Report whether the connected device has a named hardware capability.

        :param feature_name: One of "adc", "usb2_data_switch", "usb3_data_switch", "ilim_switch".

        :returns: True if the hardware capability is present, False otherwise.

        :raises FeatureNotSupportedError: If the product type or feature name is unknown.
        """
        if self.product_type is None:
            self.product_type = self.get_product_type()
        if self.product_type is None:
            raise FeatureNotSupportedError("Product type is unknown; cannot check feature support.")

        product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
        if product_info is None:
            raise FeatureNotSupportedError(f"Unknown product type: {self.product_type:#02x}")

        feature_map = {
            "adc": "enable_adc",
            "usb2_data_switch": "enable_usb2_data_switch",
            "usb3_data_switch": "enable_usb3_data_switch",
            "ilim_switch": "enable_ilim_switch",
        }
        if feature_name not in feature_map:
            raise FeatureNotSupportedError(
                f"Unknown feature name: {feature_name}. Valid features: {list(feature_map)}")
        return product_info.get(feature_map[feature_name], False)

    @classmethod
    def scan_available_ports(cls):
        """
        Scan for serial ports whose USB VID/PID match a Smart USB Hub.

        :returns: List of matching port device names.
        """
        return [p.device for p in serial.tools.list_ports.comports()
                if p.vid == 0x1A86 and p.pid == 0xfe0c]

    @classmethod
    def scan_and_connect(cls, exclude_ports=None, device_address=None):
        """
        Scan for Smart USB Hub devices and connect to the first valid one.

        :param exclude_ports: Set of ports to skip; defaults to ports already connected.

        :param device_address: If given, only connect to a device reporting this address. Note: addresses default to 0, so multiple devices may share one; prefer selecting by port. See ``scan_and_connect_by_address.``

        :returns: A connected SmartUSBHub instance, or None if none was found.
        """
        if exclude_ports is None:
            exclude_ports = cls._connected_ports.copy()

        for port_info in serial.tools.list_ports.comports():
            port_name = port_info.device
            if port_name in exclude_ports:
                logger.debug(f"Skipping already connected port {port_name}")
                continue
            if port_info.vid != 0x1A86 or port_info.pid != 0xfe0c:
                continue

            logger.debug(f"Trying to connect to port {port_name}")
            try:
                hub = cls(port_name)
                if device_address is not None and hub.device_address != device_address:
                    logger.debug(f"Address mismatch on {port_name}: "
                                 f"expected {device_address:#04x}, got {hub.device_address:#04x}")
                    hub.disconnect()
                    continue
                if device_address is not None:
                    logger.info(f"Found device with address {device_address:#04x} on port {port_name}")
                return hub
            except (SmartUSBHubError, serial.SerialException) as e:
                logger.warning(f"Failed to connect to {port_name}: {e}")
                continue

        if device_address is not None:
            logger.warning(f"No Smart USB Hub found with address {device_address:#04x}, "
                           f"or all devices are already connected.")
        else:
            logger.warning("No Smart USB Hub found, or all devices are already connected.")
        return None

    @classmethod
    def scan_and_connect_by_address(cls, device_address):
        """
        Connect to a Smart USB Hub by device address.

        .. warning::

           Addresses default to 0, so multiple devices may share one address, making this selection unreliable. Prefer ``scan_and_connect`` by port, or assign distinct addresses first.

        :param device_address: Device address to match (0x0000 - 0xFFFF).

        :returns: A connected SmartUSBHub instance, or None if no match was found.
        """
        return cls.scan_and_connect(device_address=device_address)

    @classmethod
    def auto_connect(cls, exclude_ports=None, feature_filter=None):
        """
        Scan and connect to the first available device, skipping busy ones.

        Unlike ``scan_and_connect``, a busy or failing port is skipped and the next
        candidate is tried automatically.

        :param exclude_ports: Set of ports to skip; defaults to ports already connected.

        :param feature_filter: If given, only connect to a device supporting this feature (see ``_check_feature_support`` for valid names).

        :returns: A connected SmartUSBHub instance, or None if none is available.
        """
        if exclude_ports is None:
            exclude_ports = cls._connected_ports.copy()

        ports = cls.scan_available_ports()
        if not ports:
            logger.warning("No Smart USB Hub devices found")
            return None

        logger.info(f"Found {len(ports)} device(s): {ports}")
        for port in ports:
            if port in exclude_ports:
                logger.debug(f"Skipping already connected port {port}")
                continue

            logger.info(f"Trying to connect to {port}...")
            try:
                hub = cls(port)
            except PortBusyError:
                logger.info(f"Port {port} is already in use, trying next device...")
                continue
            except (SmartUSBHubError, serial.SerialException) as e:
                logger.warning(f"Failed to connect to {port}: {e}, trying next device...")
                continue

            logger.info(f"Successfully connected to {port}")
            if feature_filter is not None and not hub._check_feature_support(feature_filter):
                logger.info(f"Device on {port} does not support '{feature_filter}', trying next device...")
                hub.disconnect()
                continue
            return hub

        logger.warning("All devices are unavailable (occupied or connection failed)")
        return None

    def _start(self):
        """
        Start the background UART receive thread.

        The thread is a daemon so it never blocks interpreter shutdown; cleanup is
        handled by ``disconnect`` and the atexit hook. Unlike earlier versions
        this no longer installs a process-wide SIGINT handler, which made the
        library unsafe to construct off the main thread or alongside other code.
        """
        self.stop_event = threading.Event()
        self.uart_recv_thread = threading.Thread(
            target=self._uart_recv_task, name=f"{self.name}-rx", daemon=True)
        self.uart_recv_thread.start()

    def disconnect(self):
        """
        Disconnect from the device and stop the receive thread.

        Idempotent and safe to call multiple times (e.g. via context-manager exit
        and atexit). Releases the port's process-local and cross-process locks.
        """
        stop_event = getattr(self, 'stop_event', None)
        if stop_event is not None:
            stop_event.set()

        thread = getattr(self, 'uart_recv_thread', None)
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1)

        ser = getattr(self, 'ser', None)
        if ser is not None and ser.is_open:
            try:
                ser.flush()
                ser.close()
            except Exception:
                pass

        SmartUSBHub._connected_ports.discard(self.port)
        SmartUSBHub._connected_addresses.pop(self.port, None)
        SmartUSBHub._instances.discard(self)
        self._release_port_lock(self.port)

    def is_connected(self):
        """
        Report whether the serial port is currently open.

        :returns: True if connected, False otherwise.
        """
        ser = getattr(self, 'ser', None)
        return bool(ser and ser.is_open)

    def _cal_crc16(self, data):
        """Compute a CRC16 (poly 0x8005, init 0xFFFF). See ``_Codec.crc16``."""
        return _Codec.crc16(data)

    def _parse_protocol_frame(self, data):
        """
        Parse one frame from the front of a received byte buffer (V1/V2/V3).

        Thin wrapper over ``_Codec.parse_frame``; see there for the frame layouts
        and the return shape.
        """
        return _Codec.parse_frame(data)

    def _uart_recv_task(self):
        """
        Background loop that reads the UART and dispatches complete frames.

        Runs until ``stop_event`` is set or the serial link fails. On an unexpected
        disconnect the registered disconnect callback (if any) is invoked.
        """
        buffer = bytearray()
        while not self.stop_event.is_set():
            try:
                if self.ser is not None and self.ser.in_waiting > 0:
                    buffer.extend(self.ser.read(self.ser.in_waiting))
                    logger.debug(f"rx data: {buffer.hex()}")

                    # Drain as many complete frames as the buffer holds. min_size
                    # is recomputed each pass so a V1 frame is not skipped after a
                    # V3 frame is consumed.
                    while True:
                        if len(buffer) < 2:
                            break
                        is_v3 = (buffer[0] == 0x55 and buffer[1] == 0xAB)
                        if is_v3:
                            # Validate the complete V3 magic before trusting the
                            # declared payload length. Otherwise a corrupt
                            # ``55 AB`` prefix with a plausible length can hold
                            # subsequent valid frames in the buffer indefinitely.
                            if len(buffer) < len(V3_MAGIC):
                                break
                            if tuple(buffer[:len(V3_MAGIC)]) != V3_MAGIC:
                                logger.debug(
                                    f"Discarding invalid V3 magic: "
                                    f"{buffer[:len(V3_MAGIC)].hex()}")
                                buffer.pop(0)
                                continue
                            if len(buffer) < V3_HEADER_LEN:
                                break
                        elif len(buffer) < 6:
                            break

                        if is_v3:
                            data_length = buffer[6] | (buffer[7] << 8)
                            if data_length > V3_MAX_DATA_LEN:
                                logger.debug(
                                    f"Discarding invalid V3 payload length: "
                                    f"{data_length} > {V3_MAX_DATA_LEN}")
                                buffer.pop(0)
                                continue
                            if len(buffer) < V3_HEADER_LEN + data_length:
                                break
                        elif buffer[0] == 0x55 and buffer[1] == 0x5A:
                            if buffer[2] in self._V2_REPLY_COMMANDS and len(buffer) < 7:
                                break

                        result = self._parse_protocol_frame(buffer)
                        if result is None:
                            buffer.pop(0)
                            continue

                        cmd, channel, value, length = result
                        logger.debug(f"Parsed cmd={cmd:#04x}, channel={channel:#04x}, "
                                     f"value={value}, raw={buffer[:length].hex()}")

                        self._dispatch_frame(cmd, channel, value)

                        del buffer[:length]
            except (OSError, AttributeError, serial.SerialException) as e:
                # errno 6 (ENXIO) and an already-set stop_event indicate an
                # expected disconnect (device reboot or explicit disconnect()).
                is_expected = self.stop_event.is_set()
                if isinstance(e, OSError) and getattr(e, 'errno', None) == 6:
                    is_expected = True

                if is_expected:
                    logger.debug(f"UART disconnected (expected): {e}")
                else:
                    logger.error(f"Error reading from UART: {e}")

                self.ser = None
                if self.disconnect_callback:
                    self.disconnect_callback()
                self.stop_event.set()
                if not is_expected:
                    logger.error("UART disconnected")
                break
            time.sleep(self._rx_poll_interval)

    def _dispatch_frame(self, cmd, channel, value):
        """
        Route one decoded frame to its state handler and ACK / wake sinks.

        This is the seam between the transport (read + frame the bytes) and the
        session (update state, satisfy waiters). Called only from the receive
        thread, one call per complete frame.
        """
        handler = self._frame_handlers.get(cmd)
        if handler is not None:
            handler(channel, value)

        # Stream frames are unsolicited notifications and must not satisfy a
        # pending ACK wait.
        is_stream_notify = (isinstance(value, dict)
                            and value.get("v3") and value.get("stream"))
        if cmd in self.ack_events and not is_stream_notify:
            self._invoke_callback(cmd, channel, value)
            self.ack_events[cmd].set()

        # Wake anyone waiting for content-based completion (see
        # _wait_for_channel_cache); cheap and unconditional.
        with self._frame_condition:
            self._frame_condition.notify_all()

    def _wait_for_channel_cache(self, cache, channels, timeout=None):
        """
        Block until every channel in ``channels`` is present in ``cache``, or timeout.

        Replaces fixed post-ACK settle delays for multi-frame replies (the device
        sends one reply frame per channel): the receive thread notifies
        ``_frame_condition`` after each frame, so this returns the instant the last
        expected channel lands — deterministic rather than guessing a delay. Callers
        should drop the stale entries for ``channels`` before sending, so a hit here
        always reflects this request's fresh frames.

        :param cache: Per-channel state dict the receive thread populates.

        :param channels: Channels that must all be present.

        :param timeout: Max wait in seconds; defaults to ``self.com_timeout.``

        :returns: True if all channels arrived, False on timeout.
        """
        if timeout is None:
            timeout = self.com_timeout
        deadline = time.monotonic() + timeout
        with self._frame_condition:
            while not all(ch in cache for ch in channels):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._frame_condition.wait(remaining)
        return True

    def _convert_channel(self, channel_mask):
        """
        Convert a channel bitmask into a list of 1-based channel numbers.

        :param channel_mask: Bitmask (bit0 = channel 1, bit1 = channel 2, ...).

        :returns: List of channel numbers present in the mask.
        """
        channels = []
        ch = 1
        while channel_mask:
            if channel_mask & 0x01:
                channels.append(ch)
            channel_mask >>= 1
            ch += 1
        return channels

    def _send_packet(self, cmd, channels, data=None):
        """
        Build and send a V1/V2 packet to the device.

        Enforces the minimum inter-command interval and post-write settle delay so
        the MCU is never overrun, even when ``ENABLE_SYNC_LOCK`` is False.

        :param cmd: Command byte.

        :param channels: Channel list, or a raw channel-mask int for CMD_SET_DEVICE_ADDRESS.

        :param data: Extra payload byte(s); defaults to a single 0x00 byte.

        :returns: The bytearray that was written.
        """
        if cmd == CMD_SET_DEVICE_ADDRESS:
            channel_mask = channels
        elif channels is None:
            channel_mask = 0
        else:
            channel_mask = sum(1 << (ch - 1) for ch in channels)

        if data is None:
            data = [0x00]
        elif not isinstance(data, list):
            data = [data]

        packet = _Codec.encode_v1v2(cmd, channel_mask, data)

        with self._send_lock:
            elapsed = time.time() - self._last_send_time
            if elapsed < self._min_send_interval:
                time.sleep(self._min_send_interval - elapsed)
            if self.ser and self.ser.is_open:
                self.ser.write(packet)
            self._last_send_time = time.time()
            time.sleep(self._mcu_response_wait)
            logger.debug(f"Sent command: {packet.hex()}")
        return packet

    def _send_v3_packet(self, cmd, payload=b""):
        """
        Build and send a V3 packet to the device.

        :param cmd: Command byte.

        :param payload: Payload as bytes, bytearray, list of ints, or a single int.

        :returns: The bytearray that was written.

        :raises ValueError: If the payload exceeds ``V3_MAX_DATA_LEN.``
        """
        packet = _Codec.encode_v3(cmd, payload)

        with self._send_lock:
            elapsed = time.time() - self._last_send_time
            if elapsed < self._min_send_interval:
                time.sleep(self._min_send_interval - elapsed)
            if self.ser and self.ser.is_open:
                self.ser.write(packet)
            self._last_send_time = time.time()
            time.sleep(self._mcu_response_wait)
            logger.debug(f"Sent V3 command: {packet.hex()}")
        return packet

    def _wait_for_ack_with_recovery(self, cmd, timeout=None):
        """
        Wait for a command ACK, triggering MCU recovery after repeated failures.

        The caller must clear ``self.ack_events[cmd]`` immediately before sending
        the command (the same discipline the get_* methods follow). This wait then
        consumes exactly that command's ACK and clears the event again on success,
        so a satisfied ACK can never leak into the next command's wait. Clearing
        before the send also discards any late ACK left over from a previously
        timed-out command, so a stale frame cannot produce a false positive.

        :param cmd: Command code to wait on.

        :param timeout: Wait timeout in seconds; defaults to ``self.com_timeout.``

        :returns: True if the ACK arrived, False on timeout.
        """
        if timeout is None:
            timeout = self.com_timeout

        ack_event = self.ack_events.get(cmd)
        if not ack_event:
            return False

        # The event was cleared before the send, so a set flag means this command's
        # ACK arrived (possibly between the send and this wait, in which case wait()
        # returns at once). Clear it again so the next reuse starts clean.
        if ack_event.wait(timeout):
            ack_event.clear()
            self._consecutive_failures = 0
            return True

        self._consecutive_failures += 1
        if self._consecutive_failures >= self._max_consecutive_failures:
            logger.warning(f"Too many consecutive failures ({self._consecutive_failures}); "
                           f"triggering MCU recovery...")
            self._trigger_mcu_recovery()
            self._consecutive_failures = 0
        return False

    def _trigger_mcu_recovery(self):
        """Give the MCU state machine time to recover and flush stale input."""
        logger.debug("Triggering MCU state-machine recovery...")
        time.sleep(0.15)  # stuck detection is 100 ms, timeout detection 20 ms
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    self.ser.reset_input_buffer()
                    logger.debug("Cleared input buffer during recovery")
            except Exception as e:
                logger.warning(f"Failed to clear input buffer: {e}")

    def _handle_set_operate_mode(self, channel, value):
        """
        --- Frame handlers ------------------------------------------------------
        Each handler updates cached state for an incoming frame. They share the
        uniform (channel, value) signature required by the dispatch table; the ACK
        Event and user callback are signalled centrally in _uart_recv_task, so
        handlers never touch ack_events themselves.

        Handle a set-operate-mode ACK (no state change).
        """
        logger.debug("set_operate_mode ACK")

    def _handle_get_operate_mode(self, channel, value):
        """Cache the operating mode from a get-operate-mode reply."""
        self.operate_mode = value

    def _handle_set_channel_power_status(self, channel, value):
        """Handle a set-channel-power ACK (no state change)."""
        logger.debug("set_channel_power ACK")

    def _handle_get_channel_power_status(self, channel, value):
        """Cache per-channel power state from a status reply."""
        for ch in self._convert_channel(channel):
            self.channel_power_status[ch] = value
            logger.debug(f"power status: ch{ch} = {value}")

    def _handle_power_interlock_control(self, channel, value):
        """Handle a power-interlock ACK (no state change)."""
        logger.debug("power_interlock ACK")

    def _handle_oc_status(self, channel, value):
        """
        Update per-channel overcurrent state from an OC status frame.

        :param channel: Active-OC bitmask (FLAG# currently asserted).

        :param value: Latched-OC bitmask (sticky until cleared).
        """
        active_mask, latch_mask = channel, value
        logger.debug(f"OC status: active=0x{active_mask:02X} latch=0x{latch_mask:02X}")
        n = self.max_channels if isinstance(self.max_channels, int) and 0 < self.max_channels <= 16 else 7
        for ch in range(1, n + 1):
            idx = ch - 1
            self.channel_oc_active[ch] = bool(active_mask & (1 << idx))
            self.channel_oc_latch[ch] = bool(latch_mask & (1 << idx))

    def _handle_get_channel_voltage(self, channel, value):
        """Cache per-channel voltage (mV) from a V2 voltage reply."""
        if isinstance(value, list) and len(value) == 2:
            mv = (value[0] << 8) | value[1]
            for ch in self._convert_channel(channel):
                self.channel_voltages[ch] = mv
                logger.debug(f"voltage: ch{ch} = {mv} mV")
        else:
            logger.error("Invalid voltage value received")

    def _handle_get_channel_current(self, channel, value):
        """Cache per-channel current (mA) from a V2 current reply."""
        if isinstance(value, list) and len(value) == 2:
            ma = (value[0] << 8) | value[1]
            for ch in self._convert_channel(channel):
                self.channel_currents[ch] = ma
                logger.debug(f"current: ch{ch} = {ma} mA")
        else:
            logger.error("Invalid current value received")

    def _handle_get_channel_measurements(self, channel, value):
        """Route a measurement frame to the V3 or legacy decoder."""
        if isinstance(value, dict) and value.get("v3"):
            self._handle_v3_measurements(value.get("payload", b""))
        else:
            self._handle_legacy_measurements(value)

    def _handle_legacy_measurements(self, value):
        """
        Decode a legacy (V2-style) batch measurement payload.

        :param value: Raw payload bytes: channel_mask [fresh_mask] then 4 bytes per channel.
        """
        if not isinstance(value, (bytes, bytearray)) or len(value) < 1:
            logger.error("Invalid measurement payload received")
            return

        channel_mask = value[0]
        channels = self._convert_channel(channel_mask)
        old_len = 1 + 4 * len(channels)
        new_len = 2 + 4 * len(channels)
        if len(value) >= new_len:
            fresh_mask, pos = value[1], 2
        elif len(value) >= old_len:
            fresh_mask, pos = channel_mask, 1
        else:
            logger.error("Truncated measurement payload received")
            return

        for ch in channels:
            if pos + 4 > len(value):
                logger.error("Truncated measurement payload received")
                break
            self.channel_voltages[ch] = (value[pos] << 8) | value[pos + 1]
            self.channel_currents[ch] = (value[pos + 2] << 8) | value[pos + 3]
            self.channel_measurement_fresh[ch] = bool(fresh_mask & (1 << (ch - 1)))
            logger.debug(f"measurement: ch{ch} = {self.channel_voltages[ch]} mV, "
                         f"{self.channel_currents[ch]} mA")
            pos += 4

    def _handle_v3_measurements(self, value):
        """
        Decode a V3 batch/stream measurement payload and notify stream waiters.

        :param value: Raw V3 payload bytes.
        """
        if not isinstance(value, (bytes, bytearray)):
            logger.error("Invalid V3 measurement response")
            return

        payload = bytes(value)
        self._last_v3_status[CMD_GET_CHANNEL_MEASUREMENTS] = V3_STATUS_OK
        if len(payload) < 8:
            logger.error("Invalid V3 measurement payload")
            return

        channel_mask = payload[0]
        fresh_mask = payload[1]
        valid_mask = payload[2]
        sample_period_ms = payload[3]
        sample_tick = (payload[4] | (payload[5] << 8)
                       | (payload[6] << 16) | (payload[7] << 24))
        pos = 8
        updated = []
        with self._measurement_stream_condition:
            for ch in self._convert_channel(channel_mask):
                if pos + 4 > len(payload):
                    logger.error("Truncated V3 measurement payload")
                    break
                self.channel_voltages[ch] = payload[pos] | (payload[pos + 1] << 8)
                self.channel_currents[ch] = payload[pos + 2] | (payload[pos + 3] << 8)
                self.channel_measurement_fresh[ch] = bool(fresh_mask & (1 << (ch - 1)))
                self.channel_measurement_valid[ch] = bool(valid_mask & (1 << (ch - 1)))
                self.channel_measurement_sample_tick[ch] = sample_tick
                updated.append(ch)
                logger.debug(f"V3 measurement: ch{ch} = {self.channel_voltages[ch]} mV, "
                             f"{self.channel_currents[ch]} mA, period={sample_period_ms} ms, "
                             f"tick={sample_tick}")
                pos += 4

            if updated:
                self._measurement_stream_tick = sample_tick
                self._measurement_stream_period_ms = sample_period_ms
                self._measurement_stream_seq += 1
                self._measurement_stream_condition.notify_all()

    def _handle_set_channel_dataline(self, channel, value):
        """Cache per-channel USB2 data-line state from a set ACK."""
        for ch in self._convert_channel(channel):
            self.channel_dataline_status[ch] = value

    def _handle_get_channel_dataline(self, channel, value):
        """Cache per-channel USB2 data-line state from a status reply."""
        for ch in self._convert_channel(channel):
            self.channel_dataline_status[ch] = value

    def _handle_get_button_control(self, channel, value):
        """Cache button-control state from a status reply."""
        self.button_control_status = value

    def _handle_set_button_control(self, channel, value):
        """Handle a set-button-control ACK (no state change)."""
        logger.debug("set_button_control ACK")

    def _store_default_status(self, channel, value, flag_dict, status_dict, label):
        """
        Cache default power flag/value for the channels in a frame.

        :param flag_dict: Destination dict for the enable flags.

        :param status_dict: Destination dict for the default values.

        :param label: Human-readable label for logging.
        """
        if isinstance(value, list) and len(value) == 2:
            enable, status = value
            for ch in self._convert_channel(channel):
                flag_dict[ch] = enable
                status_dict[ch] = status
                logger.debug(f"channel {ch} {'enable' if enable else 'disable'} default {label}, "
                             f"value: {'on' if status else 'off'}")
        else:
            logger.error(f"Invalid data for default {label} handler")

    def _handle_set_default_power_status(self, channel, value):
        """Cache default power status from a set ACK."""
        self._store_default_status(channel, value, self.channel_default_power_flag,
                                   self.channel_default_power_status, "power status")

    def _handle_get_default_power_status(self, channel, value):
        """Cache default power status from a get reply."""
        self._store_default_status(channel, value, self.channel_default_power_flag,
                                   self.channel_default_power_status, "power status")

    def _handle_set_default_dataline_status(self, channel, value):
        """Cache default data-line status from a set ACK."""
        self._store_default_status(channel, value, self.channel_default_dataline_flag,
                                   self.channel_default_dataline_status, "dataline status")

    def _handle_get_default_dataline_status(self, channel, value):
        """Cache default data-line status from a get reply."""
        self._store_default_status(channel, value, self.channel_default_dataline_flag,
                                   self.channel_default_dataline_status, "dataline status")

    def _handle_set_device_address(self, channel, value):
        """Handle a set-device-address ACK (no state change)."""
        logger.debug("set_device_address ACK")

    def _handle_get_device_address(self, channel, value):
        """Cache the device address from a reply (channel = MSB, value = LSB)."""
        self.device_address = (channel << 8) | value
        logger.debug(f"device address: {self.device_address}")

    def _handle_reboot_mcu(self, channel, value):
        """Handle a reboot-MCU ACK (no state change)."""
        logger.debug("reboot_mcu ACK")

    def _handle_identify_device(self, channel, value):
        """Handle an identify-device ACK (LED blink started on device)."""
        logger.debug("identify_device ACK")

    def _handle_channel_name(self, channel, value):
        """Cache a channel display name from a V3 response."""
        if not (isinstance(value, dict) and value.get("v3")):
            logger.debug("channel_name ACK without V3 payload")
            return
        payload = bytes(value.get("payload", b""))
        if len(payload) < 1:
            return
        ch = int(payload[0])
        if ch < 1:
            return
        try:
            name = payload[1:].decode("utf-8", errors="ignore").strip("\x00 \r\n\t")
        except Exception:
            name = ""
        self.channel_names[ch] = name or f"CH{ch}"

    def _handle_device_alias(self, channel, value):
        """Cache the device alias from a V3 response."""
        if not (isinstance(value, dict) and value.get("v3")):
            logger.debug("device_alias ACK without V3 payload")
            return
        payload = bytes(value.get("payload", b""))
        try:
            alias = payload.decode("utf-8", errors="ignore").strip("\x00 \r\n\t")
        except Exception:
            alias = ""
        self.device_alias = alias

    def _handle_factory_reset(self, channel, value):
        """Handle a factory-reset ACK (no state change)."""
        logger.debug("factory_reset ACK")

    def _handle_firmware_version(self, channel, value):
        """Cache the firmware version from a reply."""
        if isinstance(channel, int) and channel > 0:
            self.firmware_version_major = channel
            self.firmware_version_minor = value
        else:
            self.firmware_version_major = 1
            self.firmware_version_minor = value
        self.firmware_version = value

    def _handle_hardware_version(self, channel, value):
        """Cache the hardware version from a reply."""
        self.hardware_version = value

    def _handle_product_type(self, channel, value):
        """Cache the product type from a reply."""
        self.product_type = value

    def _handle_get_max_channels(self, channel, value):
        """
        Cache the maximum channel count, inferring from product type if unsupported.

        Firmware that does not support the command replies with 0xFF; in that case
        the channel count is inferred from ``PRODUCT_TYPE_TABLE`` when possible.
        """
        if value == 0xFF or value > 16:
            logger.warning(f"Suspicious max_channels value: {value} (0x{value:02X}); "
                           f"the device may not support this command.")
            if value == 0xFF and self.product_type is not None:
                product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
                if product_info is not None:
                    self.max_channels = product_info["channels"]
                    logger.info(f"Inferring max_channels={self.max_channels} "
                                f"from product type {product_info['name']}")
                    return
        self.max_channels = value

    def _handle_serial_no(self, channel, value):
        """
        Cache the serial number from a reply.

        New firmware replies with a V1 ACK whose value is the ASCII length, then
        a V3 payload containing the full serial string. Older firmware may only
        send the V1 ACK, so keep a graceful "N/A" fallback.
        """
        if isinstance(value, dict) and value.get("v3"):
            payload = value.get("payload", b"")
            try:
                serial = bytes(payload).decode("ascii", errors="ignore").strip("\x00 \r\n\t")
            except Exception:
                serial = ""
            self.serial_no = serial or "N/A"
            return
        if isinstance(value, int) and value == 0:
            self.serial_no = "N/A"

    def _handle_set_auto_restore(self, channel, value):
        """Handle a set-auto-restore ACK (no state change)."""
        logger.debug("set_auto_restore ACK")

    def _handle_get_auto_restore_status(self, channel, value):
        """Cache auto-restore state from a status reply."""
        self.auto_restore_status = value

    def _resolve_channels(self, channels):
        """
        --- Helpers -------------------------------------------------------------

        Normalize a variadic channel argument, defaulting to all channels.

        Accepts either separate channel arguments or a single iterable. When empty,
        expands to every channel the device has (from ``max_channels``, falling back
        to the product table or 7).

        :param channels: The variadic channels tuple as received by a public method.

        :returns: A tuple of 1-based channel numbers.
        """
        if len(channels) == 1 and isinstance(channels[0], (list, tuple, set)):
            channels = tuple(channels[0])
        if not channels:
            n = self.max_channels
            if not isinstance(n, int) or n <= 0 or n == 0xFF:
                product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
                n = product_info["channels"] if product_info else 7
            channels = tuple(range(1, n + 1))
        return channels

    def get_channels(self):
        """
        Return all valid 1-based channel numbers for the connected product.

        Uses the cached max-channel value when available, then falls back to
        CMD_GET_MAX_CHANNELS and finally the product capability table.

        :returns: Tuple such as (1, 2, 3, 4).

        :raises RuntimeError: If the count cannot be resolved.
        """
        n = self.max_channels
        if not isinstance(n, int) or n <= 0 or n == 0xFF:
            n = self.get_max_channels()
        if not isinstance(n, int) or n <= 0 or n == 0xFF:
            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            n = product_info["channels"] if product_info else None
        if not isinstance(n, int) or n <= 0 or n == 0xFF:
            raise RuntimeError(f"Cannot determine max channel count: {n!r}")
        return tuple(range(1, n + 1))

    def _filter_channel_dict(self, source, channels):
        """
        Build a result dict copy from a cached per-channel state dict.

        :param source: Source dict keyed by channel number.

        :param channels: Channels to include; empty means all keys in ``source.``

        :returns: A new dict containing only the requested, known channels.
        """
        if channels:
            return {ch: source[ch] for ch in channels if ch in source}
        return dict(source)

    def _measurement_snapshot(self, channels, valid_default, include_stream_meta=False):
        """
        Snapshot cached measurements for the given channels.

        :param channels: Channels to include.

        :param valid_default: Default for the "valid" flag when not yet known.

        :param include_stream_meta: Include sample_tick/sample_period_ms entries.

        :returns: Dict {channel: {voltage, current, fresh, stale, valid, ...}}.
        """
        result = {}
        for ch in channels:
            if ch not in self.channel_voltages and ch not in self.channel_currents:
                continue
            fresh = self.channel_measurement_fresh.get(ch, False)
            entry = {
                "voltage": self.channel_voltages.get(ch),
                "current": self.channel_currents.get(ch),
                "fresh": fresh,
                "stale": not fresh,
                "valid": self.channel_measurement_valid.get(ch, valid_default),
            }
            if include_stream_meta:
                entry["sample_tick"] = self.channel_measurement_sample_tick.get(ch)
                entry["sample_period_ms"] = self._measurement_stream_period_ms
            result[ch] = entry
        return result

    def _retry_get_info(self, get_func, info_name, max_retry_time=10.0):
        """
        Repeatedly call a getter until it returns non-None or the deadline passes.

        :param get_func: Zero-argument getter to retry.

        :param info_name: Label used in log messages.

        :param max_retry_time: Maximum total retry time in seconds.

        :returns: The retrieved value, or None on timeout.
        """
        start_time = time.time()
        retry_count = 0
        while True:
            result = get_func()
            if result is not None:
                logger.debug(f"{info_name} retrieved after {retry_count} retries, "
                             f"{time.time() - start_time:.2f}s")
                return result

            elapsed = time.time() - start_time
            if elapsed >= max_retry_time:
                logger.error(f"{info_name} failed after {retry_count} retries, "
                             f"{elapsed:.2f}s - giving up")
                return None

            retry_count += 1
            # Back off gradually: fast at first, then slower.
            if retry_count <= 3:
                time.sleep(0.05)
            elif retry_count <= 10:
                time.sleep(0.1)
            else:
                time.sleep(0.2)

    def _is_legacy_v1_firmware(self):
        """
        Return True when the firmware-version reply used the legacy V1 shape.

        V1 firmware reports only the minor version in the value byte and leaves
        the channel byte at zero. Newer firmware uses the channel byte as a
        major-version field, so this check does not need unsupported-command
        timeouts.
        """
        return self.firmware_version_major == 1

    def get_device_info(self):
        """
        Read and cache the hub's identity and configuration.

        Critical items (versions, operate mode, ...) are retried for up to ~10 s
        each to tolerate a device that is still initializing. Optional items not
        supported by older firmware are treated as unavailable.

        :returns: Dict describing the hub (id, address, versions, product, mode, ...).
        """
        logger.info("Reading device info (retrying up to 10s per critical item)...")

        self.hardware_version = self._retry_get_info(self.get_hardware_version, "hardware_version")
        self.firmware_version = self._retry_get_info(self.get_firmware_version, "firmware_version")

        if self._is_legacy_v1_firmware():
            self.product_type = 0x00
            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            self.max_channels = product_info["channels"] if product_info is not None else 4
            self.serial_no = "N/A"
            self.device_alias = ""
            logger.info("Legacy V1 firmware detected; using HBP_USB2_4CH defaults "
                        "without probing newer identity commands")
        else:
            self.product_type = self.get_product_type()
            if self.product_type is None:
                self.product_type = 0x00
                logger.info("CMD_GET_PRODUCT_TYPE unsupported; defaulting to HBP_USB2_4CH")

            product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
            # Optional on old firmware: infer channel count from the product type.
            self.max_channels = self.get_max_channels()
            if self.max_channels is None or self.max_channels == 0xFF:
                if product_info is not None:
                    self.max_channels = product_info["channels"]
                    logger.info(f"CMD_GET_MAX_CHANNELS unsupported; inferring "
                                f"max_channels={self.max_channels} from {product_info['name']}")

            self.serial_no = self.get_serial_no()  # optional
            self.device_alias = self.get_device_alias() or ""

        product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
        if product_info is not None:
            self.com_timeout = product_info.get("ack_timeout", 0.1)
            logger.info(f"ACK timeout set to {self.com_timeout}s for {product_info['name']}")

        self.operate_mode = self._retry_get_info(self.get_operate_mode, "operate_mode")
        self.auto_restore_status = self._retry_get_info(self.get_auto_restore_status, "auto_restore_status")
        self.button_control_status = self._retry_get_info(self.get_button_control_status, "button_control_status")
        self.device_address = self._retry_get_info(self.get_device_address, "device_address")

        # Warm the default-state caches for every channel (best effort).
        n = self.max_channels if isinstance(self.max_channels, int) and self.max_channels > 0 else 4
        channels = tuple(range(1, n + 1))
        self.get_default_power_status(*channels)
        self.get_default_dataline_status(*channels)

        product_type_name = (product_info["name"] if product_info is not None
                             else (f"Unknown({self.product_type})" if self.product_type is not None else "N/A"))
        hub_info = {
            "id": self.port.split("/")[-1],
            "address": self.device_address,
            "hardware_version": self.hardware_version,
            "firmware_version": self.firmware_version,
            "firmware_version_major": self.firmware_version_major,
            "firmware_version_minor": self.firmware_version_minor,
            "product_type": product_type_name,
            "max_channels": self.max_channels if self.max_channels is not None else "N/A",
            "serial_no": self.serial_no if self.serial_no else "N/A",
            "device_alias": self.device_alias,
            "operate_mode": ("normal" if self.operate_mode == 0
                             else "interlock" if self.operate_mode == 1 else "N/A"),
            "auto_restore": "enabled" if self.auto_restore_status == 1 else "disabled",
            "button_control_status": "enabled" if self.button_control_status == 1 else "disabled",
        }

        if self.operate_mode is None:
            logger.error("Failed to get operate mode after retries - this is critical!")
        for name in ("hardware_version", "firmware_version", "product_type",
                     "max_channels", "serial_no"):
            if getattr(self, name) is None:
                logger.warning(f"Failed to get {name} after retries")
        return hub_info

    @synchronized
    def set_operate_mode(self, mode):
        """
        Set the device operating mode.

        :param mode: ``OPERATE_MODE_NORMAL`` (0) or ``OPERATE_MODE_INTERLOCK`` (1).

        :returns: True if acknowledged, False otherwise.
        """
        self.ack_events[CMD_SET_OPERATE_MODE].clear()
        self._send_packet(CMD_SET_OPERATE_MODE, None, mode)
        if self._wait_for_ack_with_recovery(CMD_SET_OPERATE_MODE):
            return True
        logger.error("set_operate_mode No ACK!")
        return False

    @synchronized
    def get_operate_mode(self):
        """
        Query the current operating mode.

        :returns: 0 (normal), 1 (interlock), or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_OPERATE_MODE]
        ack_event.clear()
        self._send_packet(CMD_GET_OPERATE_MODE, None, None)
        if ack_event.wait(self.com_timeout):
            return self.operate_mode
        self.operate_mode = None
        logger.warning("get_operate_mode No ACK!")
        return None

    @synchronized
    def set_channel_power(self, *channels, state):
        """
        Set the power state of one or more channels.

        :param channels: Channel numbers (1-based) to update.

        :param state: 1 to power on, 0 to power off.

        :returns: True if acknowledged, False otherwise.
        """
        self.ack_events[CMD_SET_CHANNEL_POWER].clear()
        self._send_packet(CMD_SET_CHANNEL_POWER, channels, state)
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_POWER):
            return True
        logger.error("set_channel_power No ACK!")
        return False

    @synchronized
    def get_channel_power_status(self, *channels):
        """
        Query the power status of one or more channels.

        :param channels: Channels to query.

        :returns: For a single channel, its power state; for multiple, a dict {channel: state}; or None on timeout.
        """
        if len(channels) > 1:
            # Drop stale entries, then wait until every requested channel's fresh
            # reply frame has landed (deterministic; no fixed settle delay).
            for ch in channels:
                self.channel_power_status.pop(ch, None)
            self._send_packet(CMD_GET_CHANNEL_POWER_STATUS, channels)
            self._wait_for_channel_cache(self.channel_power_status, channels)
            result = {ch: self.channel_power_status[ch]
                      for ch in channels if ch in self.channel_power_status}
            return result if result else None

        ack_event = self.ack_events[CMD_GET_CHANNEL_POWER_STATUS]
        ack_event.clear()
        self._send_packet(CMD_GET_CHANNEL_POWER_STATUS, channels)
        if ack_event.wait(self.com_timeout):
            return self.channel_power_status.get(channels[0])
        logger.error("get_channel_power_status No ACK!")
        return None

    @synchronized
    def get_channel_oc_status(self):
        """
        Query per-channel overcurrent status.

        :returns: Dict {channel: {'active': bool, 'latch': bool}}, or None on timeout. 'active' is the live FLAG# state; 'latch' is sticky until cleared.
        """
        ack_event = self.ack_events[CMD_GET_CHANNEL_OC_STATUS]
        ack_event.clear()
        self._send_packet(CMD_GET_CHANNEL_OC_STATUS, None, 0)
        if ack_event.wait(self.com_timeout):
            return {ch: {'active': self.channel_oc_active.get(ch, False),
                         'latch': self.channel_oc_latch.get(ch, False)}
                    for ch in sorted(self.channel_oc_active)}
        logger.error("get_channel_oc_status No ACK!")
        return None

    @synchronized
    def clear_channel_oc_latch(self, *channels):
        """
        Clear the sticky overcurrent latch for one or more channels.

        :param channels: Channels to clear; no arguments clears all channels.

        :returns: True if acknowledged, False otherwise.
        """
        if not channels:
            n = self.max_channels if isinstance(self.max_channels, int) and 0 < self.max_channels <= 16 else 7
            channels = tuple(range(1, n + 1))
        ack_event = self.ack_events[CMD_CLEAR_CHANNEL_OC_LATCH]
        ack_event.clear()
        self._send_packet(CMD_CLEAR_CHANNEL_OC_LATCH, channels, 0)
        if ack_event.wait(self.com_timeout):
            return True
        logger.error("clear_channel_oc_latch No ACK!")
        return False

    @synchronized
    def set_channel_power_interlock(self, channel):
        """
        Set interlock mode for a channel, or release all channels.

        :param channel: Channel to interlock, or None to turn all channels off.

        :returns: True if acknowledged, False otherwise.
        """
        self.ack_events[CMD_SET_CHANNEL_POWER_INTERLOCK].clear()
        if channel is None:
            self._send_packet(CMD_SET_CHANNEL_POWER_INTERLOCK, None, 0)
        else:
            self._send_packet(CMD_SET_CHANNEL_POWER_INTERLOCK, [channel], 1)
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_POWER_INTERLOCK):
            return True
        logger.error("set_channel_power_interlock No ACK!")
        return False

    def _raise_adc_unsupported(self):
        """
        Raise a descriptive error when the model lacks ADC monitoring.

        :raises FeatureNotSupportedError: Always.
        """
        product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
        product_name = product_info["name"] if product_info else f"Unknown({self.product_type:#02x})"
        raise FeatureNotSupportedError(
            f"Product {product_name} does not support voltage/current monitoring (ADC). "
            f"This feature is not available on this device model.")

    @synchronized
    def get_channel_voltage(self, channel):
        """
        Read the voltage of a single channel.

        :param channel: Channel to query.

        :returns: Voltage in mV, or None on timeout.

        :raises FeatureNotSupportedError: If the model lacks ADC monitoring.

        :raises ValueError: If a list/tuple is passed instead of a single channel.
        """
        if isinstance(channel, (list, tuple)):
            raise ValueError("get_channel_voltage only supports a single channel")
        if not self._check_feature_support("adc"):
            self._raise_adc_unsupported()

        ack_event = self.ack_events[CMD_GET_CHANNEL_VOLTAGE]
        ack_event.clear()
        self._send_packet(CMD_GET_CHANNEL_VOLTAGE, [channel])
        if ack_event.wait(self.com_timeout):
            return self.channel_voltages.get(channel)
        logger.error("get_channel_voltage No ACK!")
        return None

    @synchronized
    def get_channel_current(self, channel):
        """
        Read the current of a single channel.

        :param channel: Channel to query.

        :returns: Current in mA, or None on timeout.

        :raises FeatureNotSupportedError: If the model lacks ADC monitoring.

        :raises ValueError: If a list/tuple is passed instead of a single channel.
        """
        if isinstance(channel, (list, tuple)):
            raise ValueError("get_channel_current only supports a single channel")
        if not self._check_feature_support("adc"):
            self._raise_adc_unsupported()

        ack_event = self.ack_events[CMD_GET_CHANNEL_CURRENT]
        ack_event.clear()
        self._send_packet(CMD_GET_CHANNEL_CURRENT, [channel])
        if ack_event.wait(self.com_timeout):
            return self.channel_currents.get(channel)
        logger.error("get_channel_current No ACK!")
        return None

    @synchronized
    def get_channel_measurements(self, *channels):
        """
        Read voltage/current for multiple channels in one V3 request.

        :param channels: Channels to query; if omitted, all channels are queried.

        :returns: Dict {channel: {"voltage", "current", "fresh", "stale", "valid"}}, or None on timeout.

        :raises FeatureNotSupportedError: If the model lacks ADC monitoring.
        """
        if not self._check_feature_support("adc"):
            self._raise_adc_unsupported()
        channels = self._resolve_channels(channels)

        if self._is_legacy_v1_firmware():
            result = {}
            for ch in channels:
                voltage_event = self.ack_events[CMD_GET_CHANNEL_VOLTAGE]
                voltage_event.clear()
                self._send_packet(CMD_GET_CHANNEL_VOLTAGE, [ch])
                if not voltage_event.wait(self.com_timeout):
                    logger.error("get_channel_measurements legacy voltage No ACK!")
                    return None

                current_event = self.ack_events[CMD_GET_CHANNEL_CURRENT]
                current_event.clear()
                self._send_packet(CMD_GET_CHANNEL_CURRENT, [ch])
                if not current_event.wait(self.com_timeout):
                    logger.error("get_channel_measurements legacy current No ACK!")
                    return None

                result[ch] = {
                    "voltage": self.channel_voltages.get(ch),
                    "current": self.channel_currents.get(ch),
                    "fresh": True,
                    "stale": False,
                    "valid": True,
                }
            return result

        ack_event = self.ack_events[CMD_GET_CHANNEL_MEASUREMENTS]
        channel_mask = sum(1 << (ch - 1) for ch in channels)
        for attempt in range(3):
            ack_event.clear()
            self._send_v3_packet(CMD_GET_CHANNEL_MEASUREMENTS, [channel_mask, 0x00])
            if ack_event.wait(self.com_timeout):
                if self._last_v3_status.get(CMD_GET_CHANNEL_MEASUREMENTS) == V3_STATUS_OK:
                    result = self._measurement_snapshot(channels, valid_default=True)
                    has_fresh = any(item["fresh"] for item in result.values())
                    if result and any(item["valid"] for item in result.values()) and has_fresh:
                        return result
                    if attempt < 2:
                        time.sleep(0.06)
                        continue
                    logger.warning("V3 measurement response contained no valid channel data")
                else:
                    logger.warning("V3 measurement command returned an error")
                break
            if attempt < 2:
                time.sleep(0.02)

        logger.error("get_channel_measurements No ACK!")
        return None

    def get_stream_channel_measurements(self, *channels, timeout=None, wait_new_sample=True):
        """
        Wait for the next V3 measurement stream frame and return its readings.

        Does not send a request; the device must already have streaming enabled via
        ``set_channel_measurement_stream.``

        :param channels: Channels to include; if omitted, all channels.

        :param timeout: Wait timeout in seconds; defaults to ``self.com_timeout.``

        :param wait_new_sample: If True, wait for a new sample tick; if False, accept the next stream frame even with the same tick.

        :returns: Dict of per-channel readings (with sample_tick/sample_period_ms), or None.
        """
        channels = self._resolve_channels(channels)
        if timeout is None:
            timeout = self.com_timeout

        deadline = time.monotonic() + timeout
        with self._measurement_stream_condition:
            start_seq = self._measurement_stream_seq
            start_tick = self._measurement_stream_tick
            while True:
                has_channels = any(ch in self.channel_voltages or ch in self.channel_currents
                                   for ch in channels)
                got_new_frame = self._measurement_stream_seq != start_seq
                got_new_sample = (self._measurement_stream_tick is not None
                                  and (start_tick is None
                                       or self._measurement_stream_tick != start_tick))
                if has_channels and (got_new_sample if wait_new_sample else got_new_frame):
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                self._measurement_stream_condition.wait(remaining)

            return self._measurement_snapshot(channels, valid_default=False, include_stream_meta=True)

    @synchronized
    def set_channel_measurement_stream(self, *channels, enabled=True, wait_ack=True):
        """
        Enable or disable V3 measurement streaming.

        Stream frames are unsolicited V3 notifications and are not acknowledged by
        the host.

        :param channels: Channels to stream; if omitted, all channels.

        :param enabled: True to enable streaming, False to disable.

        :param wait_ack: If True, wait for the command ACK before returning.

        :returns: True on success (or when ``wait_ack`` is False), False on timeout.
        """
        channels = self._resolve_channels(channels)
        channel_mask = sum(1 << (ch - 1) for ch in channels)
        flags = V3_MEAS_FLAG_STREAM_ENABLE if enabled else V3_MEAS_FLAG_STREAM_DISABLE
        ack_event = self.ack_events[CMD_GET_CHANNEL_MEASUREMENTS]
        ack_event.clear()
        self._send_v3_packet(CMD_GET_CHANNEL_MEASUREMENTS, [channel_mask, flags])
        if not wait_ack:
            return True
        if ack_event.wait(self.com_timeout):
            return True
        logger.error("set_channel_measurement_stream No ACK!")
        return False

    def get_latest_measurements(self, *channels):
        """
        Return the most recently received measurements without blocking.

        Returns whatever the background receiver has cached. Requires that
        streaming was started via ``set_channel_measurement_stream.``

        :param channels: Channels to include; if omitted, all channels.

        :returns: Dict of per-channel readings, or None if nothing has been received.
        """
        channels = self._resolve_channels(channels)
        with self._measurement_stream_condition:
            result = self._measurement_snapshot(channels, valid_default=False, include_stream_meta=True)
        return result if result else None

    @synchronized
    def set_channel_usb2_dataline(self, *channels, state):
        """
        Set the USB2.0 data-line state of one or more channels.

        :param channels: Channels to update.

        :param state: 1 to connect the data line, 0 to disconnect.

        :returns: True if acknowledged, False otherwise.
        """
        self.ack_events[CMD_SET_CHANNEL_DATALINE].clear()
        self._send_packet(CMD_SET_CHANNEL_DATALINE, channels, state)
        if self._wait_for_ack_with_recovery(CMD_SET_CHANNEL_DATALINE):
            return True
        logger.error("set_channel_usb2_dataline No ACK!")
        return False

    def set_channel_dataline(self, *channels, state):
        """
        Backward-compatible alias for the V1 API name.

        Older releases exposed USB2 data-line control as
        ``set_channel_dataline``. Keep that spelling available while the newer
        API uses ``set_channel_usb2_dataline`` for clarity.
        """
        return self.set_channel_usb2_dataline(*channels, state=state)

    @synchronized
    def get_channel_usb2_dataline_status(self, *channels):
        """
        Query the USB2.0 data-line status of one or more channels.

        :param channels: Channels to query; if omitted, returns all known channels.

        :returns: Dict {channel: state} for the requested channels, or None on timeout.
        """
        if len(channels) > 1:
            # Drop stale entries, then wait until every requested channel's fresh
            # reply frame has landed (deterministic; no fixed settle delay).
            for ch in channels:
                self.channel_dataline_status.pop(ch, None)
            self._send_packet(CMD_GET_CHANNEL_DATALINE_STATUS, channels)
            self._wait_for_channel_cache(self.channel_dataline_status, channels)
            result = self._filter_channel_dict(self.channel_dataline_status, channels)
            return result if result else None

        ack_event = self.ack_events[CMD_GET_CHANNEL_DATALINE_STATUS]
        ack_event.clear()
        self._send_packet(CMD_GET_CHANNEL_DATALINE_STATUS, channels)
        if ack_event.wait(self.com_timeout):
            return self._filter_channel_dict(self.channel_dataline_status, channels)
        logger.error("get_channel_usb2_dataline_status No ACK!")
        return None

    def get_channel_dataline_status(self, *channels):
        """
        Backward-compatible alias for the V1 API name.

        Older releases exposed USB2 data-line status as
        ``get_channel_dataline_status``. Keep that spelling available while the
        newer API uses ``get_channel_usb2_dataline_status`` for clarity.
        """
        return self.get_channel_usb2_dataline_status(*channels)

    @synchronized
    def set_button_control(self, enable: bool):
        """
        Enable or disable the hub's physical buttons.

        :param enable: True to enable buttons, False to disable.

        :returns: True if acknowledged, False otherwise.
        """
        self.ack_events[CMD_SET_BUTTON_CONTROL].clear()
        self._send_packet(CMD_SET_BUTTON_CONTROL, None, 1 if enable else 0)
        if self._wait_for_ack_with_recovery(CMD_SET_BUTTON_CONTROL):
            return True
        logger.error("set_button_control No ACK!")
        return False

    @synchronized
    def get_button_control_status(self):
        """
        Query whether the hub's physical buttons are enabled.

        :returns: 1 if enabled, 0 if disabled, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_BUTTON_CONTROL_STATUS]
        ack_event.clear()
        self._send_packet(CMD_GET_BUTTON_CONTROL_STATUS, None, None)
        if ack_event.wait(self.com_timeout):
            return self.button_control_status
        logger.error("get_button_control_status No ACK!")
        return None

    @synchronized
    def set_default_power_status(self, *channels, enable, status=None):
        """
        Set the power-on default power state for one or more channels.

        :param channels: Channels to configure.

        :param enable: 1 to apply a default power state, 0 to disable defaulting.

        :param status: Default state when enabled: 1 for ON, 0 for OFF (default 0).

        :returns: True if acknowledged, False otherwise.
        """
        if status is None:
            status = 0
        self.ack_events[CMD_SET_DEFAULT_POWER_STATUS].clear()
        self._send_packet(CMD_SET_DEFAULT_POWER_STATUS, channels, [enable, status])
        if self._wait_for_ack_with_recovery(CMD_SET_DEFAULT_POWER_STATUS):
            return True
        logger.error("set_default_power_status No ACK!")
        return False

    @synchronized
    def get_default_power_status(self, *channels):
        """
        Query the default power configuration for one or more channels.

        :param channels: Channels to query.

        :returns: Dict {channel: {"enabled", "value"}}, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_DEFAULT_POWER_STATUS]
        ack_event.clear()
        self._send_packet(CMD_GET_DEFAULT_POWER_STATUS, channels, [0, 0])
        if ack_event.wait(self.com_timeout):
            result = {}
            for ch in channels:
                enable = self.channel_default_power_flag.get(ch)
                status = self.channel_default_power_status.get(ch)
                if enable is not None and status is not None:
                    result[ch] = {"enabled": enable, "value": status}
            return result
        logger.error("get_default_power_status No ACK!")
        return None

    @synchronized
    def set_default_dataline_status(self, *channels, enable, status=None):
        """
        Set the power-on default data-line state for one or more channels.

        :param channels: Channels to configure.

        :param enable: 1 to apply a default data-line state, 0 to disable defaulting.

        :param status: Default state when enabled: 1 for connected, 0 for disconnected (default 0).

        :returns: True if acknowledged, False otherwise.
        """
        if status is None:
            status = 0
        self.ack_events[CMD_SET_DEFAULT_DATALINE_STATUS].clear()
        self._send_packet(CMD_SET_DEFAULT_DATALINE_STATUS, channels, [enable, status])
        if self._wait_for_ack_with_recovery(CMD_SET_DEFAULT_DATALINE_STATUS):
            return True
        logger.error("set_default_dataline_status No ACK!")
        return False

    @synchronized
    def get_default_dataline_status(self, *channels):
        """
        Query the default data-line configuration for one or more channels.

        :param channels: Channels to query.

        :returns: Dict {channel: {"enabled", "value"}}, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_DEFAULT_DATALINE_STATUS]
        ack_event.clear()
        self._send_packet(CMD_GET_DEFAULT_DATALINE_STATUS, channels, [0, 0])
        if ack_event.wait(self.com_timeout):
            result = {}
            for ch in channels:
                enable = self.channel_default_dataline_flag.get(ch)
                status = self.channel_default_dataline_status.get(ch)
                if enable is not None and status is not None:
                    result[ch] = {"enabled": enable, "value": status}
            return result
        logger.error("get_default_dataline_status No ACK!")
        return None

    @synchronized
    def set_auto_restore(self, enable: bool):
        """
        Enable or disable the auto-restore feature.

        :param enable: True to enable auto-restore, False to disable.

        :returns: True if acknowledged, False otherwise.
        """
        self.ack_events[CMD_SET_AUTO_RESTORE].clear()
        self._send_packet(CMD_SET_AUTO_RESTORE, None, 1 if enable else 0)
        if self._wait_for_ack_with_recovery(CMD_SET_AUTO_RESTORE):
            return True
        logger.error("set_auto_restore No ACK!")
        return False

    @synchronized
    def get_auto_restore_status(self):
        """
        Query whether auto-restore is enabled.

        :returns: 1 if enabled, 0 if disabled, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_AUTO_RESTORE_STATUS]
        ack_event.clear()
        self._send_packet(CMD_GET_AUTO_RESTORE_STATUS, None, None)
        if ack_event.wait(self.com_timeout):
            return self.auto_restore_status
        logger.error("get_auto_restore_status No ACK!")
        return None

    @synchronized
    def set_device_address(self, address: int):
        """
        Set the 16-bit device address.

        :param address: Address in the range 0x0000 - 0xFFFF.

        :returns: True if acknowledged, False otherwise.

        :raises ValueError: If the address is out of range.
        """
        if not (0 <= address <= 0xFFFF):
            raise ValueError("Address must be between 0x0000 and 0xFFFF")
        lsb = address & 0xFF
        msb = (address >> 8) & 0xFF
        ack_event = self.ack_events[CMD_SET_DEVICE_ADDRESS]
        ack_event.clear()
        self._send_packet(CMD_SET_DEVICE_ADDRESS, msb, lsb)
        if ack_event.wait(self.com_timeout):
            self.device_address = address
            return True
        logger.error("set_device_address No ACK!")
        return False

    @synchronized
    def get_device_address(self):
        """
        Query the current device address.

        :returns: The 16-bit device address, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_DEVICE_ADDRESS]
        ack_event.clear()
        self._send_packet(CMD_GET_DEVICE_ADDRESS, None, None)
        if ack_event.wait(self.com_timeout):
            return self.device_address
        logger.error("get_device_address No ACK!")
        return None

    @synchronized
    def reboot_mcu(self):
        """
        Reboot the device MCU.

        The MCU reboots ~100 ms after acknowledging, so the connection is lost and
        the device must typically be reconnected afterwards.

        :returns: True if the reboot command was acknowledged, False otherwise.
        """
        ack_event = self.ack_events[CMD_REBOOT_MCU]
        ack_event.clear()
        # Catch an ACK that may already be in flight.
        time.sleep(0.001)
        if ack_event.is_set():
            ack_event.clear()
            return True

        self._send_packet(CMD_REBOOT_MCU, None, None)
        # Longer timeout: the MCU delays ~100 ms after the ACK before rebooting.
        if ack_event.wait(0.2):
            return True
        logger.error("reboot_mcu No ACK!")
        return False

    @synchronized
    def factory_reset(self):
        """
        Reset the device to factory settings.

        :returns: True if acknowledged, False otherwise.
        """
        ack_event = self.ack_events[CMD_FACTORY_RESET]
        ack_event.clear()
        self._send_packet(CMD_FACTORY_RESET, None, None)
        if ack_event.wait(self.com_timeout):
            return True
        logger.error("factory_reset No ACK!")
        return False

    @synchronized
    def identify_device(self):
        """
        Blink the device status LED quickly for a few seconds.

        :returns: True if acknowledged, False otherwise.
        """
        ack_event = self.ack_events[CMD_IDENTIFY_DEVICE]
        ack_event.clear()
        self._send_packet(CMD_IDENTIFY_DEVICE, None, None)
        if ack_event.wait(self.com_timeout):
            return True
        logger.error("identify_device No ACK!")
        return False

    @staticmethod
    def _default_channel_name(channel):
        return f"CH{int(channel)}"

    @staticmethod
    def _encode_utf8_fit(text, max_bytes):
        data = str(text or "").strip().encode("utf-8")[:max_bytes]
        while True:
            try:
                data.decode("utf-8")
                return data
            except UnicodeDecodeError:
                data = data[:-1]

    @staticmethod
    def _encode_channel_name(name):
        return SmartUSBHub._encode_utf8_fit(name, 15)

    @staticmethod
    def _encode_device_alias(alias):
        return SmartUSBHub._encode_utf8_fit(alias, 31)

    @synchronized
    def set_device_alias(self, alias):
        """
        Store a custom device alias in the device.

        Empty aliases clear the custom alias. Alias is UTF-8, up to 31 bytes.

        :returns: True if acknowledged, False otherwise.
        """
        ack_event = self.ack_events[CMD_SET_DEVICE_ALIAS]
        ack_event.clear()
        self.device_alias = ""
        self._send_v3_packet(CMD_SET_DEVICE_ALIAS, self._encode_device_alias(alias))
        if ack_event.wait(max(0.2, self.com_timeout)):
            return True
        logger.error("set_device_alias No ACK!")
        return False

    @synchronized
    def get_device_alias(self):
        """
        Query the custom device alias.

        :returns: Alias string, "" when unset, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_DEVICE_ALIAS]
        ack_event.clear()
        self.device_alias = ""
        self._send_v3_packet(CMD_GET_DEVICE_ALIAS, b"")
        if ack_event.wait(max(0.2, self.com_timeout)):
            return self.device_alias or ""
        logger.debug("get_device_alias No ACK (may be old firmware)")
        return ""

    @synchronized
    def set_channel_name(self, channel, name):
        """
        Store a custom channel display name in the device.

        Empty names clear the custom name and make the device fall back to CHn.
        Names are stored as UTF-8, up to 15 bytes.

        :returns: True if acknowledged, False otherwise.
        """
        channel = int(channel)
        if channel < 1:
            raise ValueError("channel must be >= 1")
        ack_event = self.ack_events[CMD_SET_CHANNEL_NAME]
        ack_event.clear()
        self.channel_names.pop(channel, None)
        payload = bytes([channel]) + self._encode_channel_name(name)
        self._send_v3_packet(CMD_SET_CHANNEL_NAME, payload)
        if ack_event.wait(max(0.2, self.com_timeout)):
            return True
        logger.error("set_channel_name No ACK!")
        return False

    @synchronized
    def get_channel_name(self, channel):
        """
        Query a channel display name from the device.

        :returns: Stored name, default CHn, or None if no response.
        """
        channel = int(channel)
        if channel < 1:
            raise ValueError("channel must be >= 1")
        ack_event = self.ack_events[CMD_GET_CHANNEL_NAME]
        ack_event.clear()
        self.channel_names.pop(channel, None)
        self._send_v3_packet(CMD_GET_CHANNEL_NAME, [channel])
        if ack_event.wait(max(0.2, self.com_timeout)):
            return self.channel_names.get(channel, self._default_channel_name(channel))
        logger.debug("get_channel_name No ACK (may be old firmware)")
        return self._default_channel_name(channel)

    def get_channel_names(self, *channels):
        """Query display names for one or more channels."""
        resolved = self._resolve_channels(channels)
        return {ch: self.get_channel_name(ch) for ch in resolved}

    @synchronized
    def get_firmware_version(self):
        """
        Query the firmware version.

        :returns: The firmware version, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_FIRMWARE_VERSION]
        ack_event.clear()
        self._send_packet(CMD_GET_FIRMWARE_VERSION, None, None)
        if ack_event.wait(self.com_timeout):
            return self.firmware_version
        logger.error("get_firmware_version No ACK!")
        return None

    def get_firmware_version_major(self):
        """
        Return the cached firmware major version, querying the device if needed.

        Older firmware replies only with the minor version byte; those devices
        are treated as major version 1 for backward compatibility.
        """
        if self.firmware_version_major is None:
            self.get_firmware_version()
        return self.firmware_version_major

    def get_firmware_version_string(self):
        """Return a display string such as ``V2.1`` for the cached firmware.

        Format is ``V<major>.<minor>`` (minor is NOT zero-padded), e.g. major=2
        minor=1 -> ``V2.1``. (Older builds padded the minor to two digits, which
        rendered as the confusing ``V2.01``.)
        """
        major = self.firmware_version_major if self.firmware_version_major is not None else 1
        minor = self.firmware_version_minor
        if minor is None:
            minor = self.firmware_version
        if minor is None:
            return "Unknown"
        return f"V{major}.{minor}"

    @synchronized
    def get_hardware_version(self):
        """
        Query the hardware version.

        :returns: The hardware version, or None if no response.
        """
        ack_event = self.ack_events[CMD_GET_HARDWARE_VERSION]
        ack_event.clear()
        self._send_packet(CMD_GET_HARDWARE_VERSION, None, None)
        if ack_event.wait(self.com_timeout):
            return self.hardware_version
        logger.error("get_hardware_version No ACK!")
        return None

    @synchronized
    def get_product_type(self):
        """
        Query the product-type ID.

        Optional command: older firmware does not respond, in which case None is
        returned (logged at debug level, not as an error).

        :returns: The product-type ID, or None if unsupported/no response.
        """
        ack_event = self.ack_events[CMD_GET_PRODUCT_TYPE]
        ack_event.clear()
        self._send_packet(CMD_GET_PRODUCT_TYPE, None, None)
        if ack_event.wait(self.com_timeout):
            return self.product_type
        logger.debug("get_product_type No ACK (may be old firmware)")
        return None

    @synchronized
    def get_product_name(self):
        """
        Get the product name for the connected device.

        :returns: The product name (e.g. "HBP_USB2_4CH"), an "Unknown(...)" string, or None if the product type is unavailable.
        """
        if self.product_type is None:
            self.product_type = self.get_product_type()
        if self.product_type is None:
            return None
        product_info = PRODUCT_TYPE_TABLE.get(self.product_type)
        return product_info["name"] if product_info is not None else f"Unknown({self.product_type:#02x})"

    @synchronized
    def get_max_channels(self):
        """
        Query the maximum channel count.

        Optional command: older firmware does not respond, in which case None is
        returned (logged at debug level, not as an error).

        :returns: The maximum channel count, or None if unsupported/no response.
        """
        ack_event = self.ack_events[CMD_GET_MAX_CHANNELS]
        ack_event.clear()
        self._send_packet(CMD_GET_MAX_CHANNELS, None, None)
        if ack_event.wait(self.com_timeout):
            return self.max_channels
        logger.debug("get_max_channels No ACK (may be old firmware)")
        return None

    @synchronized
    def get_serial_no(self):
        """
        Query the device serial number.

        :returns: The serial-number string ("N/A" if unavailable), or None if no response.
        """
        if self._is_legacy_v1_firmware():
            self.serial_no = self.serial_no or "N/A"
            return self.serial_no

        ack_event = self.ack_events[CMD_GET_SERIAL_NO]
        ack_event.clear()
        self.serial_no = None
        self._send_packet(CMD_GET_SERIAL_NO, None, None)
        if ack_event.wait(self.com_timeout):
            deadline = time.time() + max(0.2, self.com_timeout)
            while self.serial_no is None and time.time() < deadline:
                time.sleep(0.01)
            return self.serial_no
        logger.debug("get_serial_no No ACK (may be old firmware)")
        return None


# Disconnect every open instance on interpreter exit as a safety net for callers
# that forget to disconnect() or use the context-manager form.
atexit.register(SmartUSBHub._cleanup_all_instances)
