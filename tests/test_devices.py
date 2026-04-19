import pytest
from unittest.mock import MagicMock, patch
from k70corergb.device import Device, DeviceNotFoundError, DeviceError, CORSAIR_VID, K70_CORE_TKL_PID
from k70corergb.protocol import PACKET_SIZE

_FAKE_PATH = b"/dev/hidraw0"

_MATCHING_DEVICE = {
    "vendor_id": CORSAIR_VID,
    "product_id": K70_CORE_TKL_PID,
    "path": _FAKE_PATH,
    "usage_page": 0x0006,
    "interface_number": 1,
}


def _make_device(mock_hid) -> Device:
    mock_hid.enumerate.return_value = [_MATCHING_DEVICE]
    mock_hid.device.return_value = MagicMock()
    dev = Device()
    dev.open()
    return dev


class TestDeviceOpen:
    def test_opens_successfully(self):
        with patch("k70corergb.device.hid") as mock_hid:
            dev = _make_device(mock_hid)
            assert dev._dev is not None

    def test_open_twice_is_idempotent(self):
        with patch("k70corergb.device.hid") as mock_hid:
            dev = _make_device(mock_hid)
            dev.open()
            mock_hid.device.assert_called_once()

    def test_no_device_raises(self):
        with patch("k70corergb.device.hid") as mock_hid:
            mock_hid.enumerate.return_value = []
            with pytest.raises(DeviceNotFoundError):
                Device().open()

    def test_os_error_raises_device_error(self):
        with patch("k70corergb.device.hid") as mock_hid:
            mock_hid.enumerate.return_value = [_MATCHING_DEVICE]
            mock_dev = MagicMock()
            mock_dev.open_path.side_effect = OSError("permission denied")
            mock_hid.device.return_value = mock_dev
            with pytest.raises(DeviceError):
                Device().open()


class TestDeviceClose:
    def test_close_clears_device(self):
        with patch("k70corergb.device.hid") as mock_hid:
            dev = _make_device(mock_hid)
            dev.close()
            assert dev._dev is None

    def test_close_when_not_open_is_safe(self):
        Device().close()


class TestDeviceWrite:
    def test_write_sends_report_with_zero_prefix(self):
        with patch("k70corergb.device.hid") as mock_hid:
            dev = _make_device(mock_hid)
            packet = bytes(PACKET_SIZE)
            dev.write(packet)
            dev._dev.write.assert_called_once_with(b"\x00" + packet)

    def test_write_wrong_size_raises(self):
        with patch("k70corergb.device.hid") as mock_hid:
            dev = _make_device(mock_hid)
            with pytest.raises(ValueError):
                dev.write(bytes(32))

    def test_write_when_closed_raises(self):
        with pytest.raises(DeviceError):
            Device().write(bytes(PACKET_SIZE))

    def test_write_os_error_raises_device_error(self):
        with patch("k70corergb.device.hid") as mock_hid:
            dev = _make_device(mock_hid)
            dev._dev.write.side_effect = OSError("pipe broken")
            with pytest.raises(DeviceError):
                dev.write(bytes(PACKET_SIZE))

    def test_write_all_sends_each_packet(self):
        with patch("k70corergb.device.hid") as mock_hid:
            dev = _make_device(mock_hid)
            packets = [bytes(PACKET_SIZE)] * 7
            dev.write_all(packets)
            assert dev._dev.write.call_count == 7


class TestDeviceContextManager:
    def test_context_manager_opens_and_closes(self):
        with patch("k70corergb.device.hid") as mock_hid:
            mock_hid.enumerate.return_value = [_MATCHING_DEVICE]
            mock_hid.device.return_value = MagicMock()
            with Device() as dev:
                assert dev._dev is not None
            assert dev._dev is None