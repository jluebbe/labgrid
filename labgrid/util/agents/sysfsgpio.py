"""
This module implements switching GPIOs via sysfs GPIO kernel interface.

Takes an integer property 'index' which refers to the already exported GPIO device.

"""
import logging
import os

class GpioDigitalOutput:
    _gpio_sysfs_path_prefix = '/sys/class/gpio'
    _buffered_file_access=False

    def _assert_gpio_line_is_exported(index):
        gpio_sysfs_path = os.path.join(GpioDigitalOutput._gpio_sysfs_path_prefix, 'gpio{0}'.format(index))
        if not os.path.exists(gpio_sysfs_path):
            export_sysfs_path = os.path.join(GpioDigitalOutput._gpio_sysfs_path_prefix, 'export')
            with open(export_sysfs_path, mode = 'r+', buffering = GpioDigitalOutput._buffered_file_access, closefd = True) as export:
                export.write(str(index))
        if not os.path.exists(gpio_sysfs_path):
            raise ValueError("Device not found")

    def __init__(self, **kwargs):
        index = kwargs['index']
        self._logger = logging.getLogger("Device: ")
        GpioDigitalOutput._assert_gpio_line_is_exported(index)
        gpio_sysfs_path = os.path.join(GpioDigitalOutput._gpio_sysfs_path_prefix, 'gpio{0}'.format(index))
        gpio_sysfs_direction_path = os.path.join(gpio_sysfs_path, 'direction')
        self._logger.debug("Configuring GPIO {idx} as output.".format(idx = index))
        with open(gpio_sysfs_direction_path, 'wb') as direction_fd:
            direction_fd.write(b'out')
        gpio_sysfs_value_path = os.path.join(gpio_sysfs_path, 'value')
        self.gpio_sysfs_value_fd = os.open(gpio_sysfs_value_path, flags=(os.O_RDWR | os.O_SYNC))

    def __del__(self):
        os.close(self.gpio_sysfs_value_fd)
        self.gpio_sysfs_value_fd = None

    def get(self):
        os.lseek(self.gpio_sysfs_value_fd, 0, os.SEEK_SET)
        literal_value = os.read(self.gpio_sysfs_value_fd, 1)
        if literal_value == b'0':
            return False
        elif literal_value == b'1':
            return True
        raise ValueError("GPIO value is out of range.")

    def set(self, status):
        self._logger.debug(
                "Setting GPIO to `{}`.".format(status))
        binary_value = None
        if status is True:
            binary_value = b'1'
        elif status is False:
            binary_value = b'0'

        if binary_value is None:
            raise ValueError("GPIO value is out of range.")

        os.write(self.gpio_sysfs_value_fd, binary_value)


_gpios = {}

def _get_gpio_line(_index):
    if _index not in _gpios:
        _gpios[_index] = GpioDigitalOutput(index = _index)
    return _gpios[_index]

def handle_set(index, status):
    gpio_line = _get_gpio_line(index)
    gpio_line.set(status)


def handle_get(index):
    gpio_line = _get_gpio_line(index)
    return gpio_line.get()


methods = {
    'set': handle_set,
    'get': handle_get,
}
