# pylint: disable=no-member
import attr

from .common import Driver
from ..factory import target_factory
from ..step import step
from ..util.agentwrapper import AgentWrapper
from ..resource.remote import RemoteNetworkInterface


@target_factory.reg_driver
@attr.s(eq=False)
class NetworkInterfaceDriver(Driver):
    bindings = {
        "iface": {"RemoteNetworkInterface", "USBNetworkInterface"},
    }

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.wrapper = None

    def on_activate(self):
        if isinstance(self.iface, RemoteNetworkInterface):
            host = self.iface.host
        else:
            host = None
        self.wrapper = AgentWrapper(host)
        self.proxy = self.wrapper.load('network_interface')

    def on_deactivate(self):
        try:
            self.proxy.disable(self.iface.ifname)
        finally:
            self.wrapper.close()
            self.wrapper = None
            self.proxy = None

    # basic
    @Driver.check_active
    @step()
    def configure(self, settings):
        self.proxy.configure(self.iface.ifname, settings)

    @Driver.check_active
    @step()
    def wait_state(self, expected, timeout=60):
        self.proxy.wait_state(self.iface.ifname, expected, timeout)

    @Driver.check_active
    @step()
    def disable(self):
        self.proxy.disable(self.iface.ifname)

    @Driver.check_active
    @step()
    def get_active_settings(self):
        return self.proxy.get_active_settings(self.iface.ifname)

    @Driver.check_active
    @step()
    def get_settings(self):
        return self.proxy.get_settings(self.iface.ifname)

    @Driver.check_active
    @step()
    def get_state(self):
        return self.proxy.get_state(self.iface.ifname)

    # dhcpd
    @Driver.check_active
    @step()
    def get_dhcpd_leases(self):
        return self.proxy.get_dhcpd_leases(self.iface.ifname)

    # wireless
    @Driver.check_active
    @step()
    def request_scan(self):
        return self.proxy.request_scan(self.iface.ifname)

    @Driver.check_active
    @step()
    def get_access_points(self, scan=None):
        return self.proxy.get_access_points(self.iface.ifname, scan)

