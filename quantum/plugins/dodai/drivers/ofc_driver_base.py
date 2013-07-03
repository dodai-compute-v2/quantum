# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 National Institute of Informatics.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from abc import ABCMeta, abstractmethod


class OFCDriverBase(object):
    """
    OpenFlow Controller (OFC) Driver Specification.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def create_region(self, region_name):
        pass

    @abstractmethod
    def destroy_region(self, region_name):
        pass

    @abstractmethod
    def show_region(self):
        pass

    @abstractmethod
    def set_server_port(self, dpid, server_port, region_name):
        pass

    @abstractmethod
    def clear_server_port(self, dpid, server_port):
        pass

    @abstractmethod
    def show_switch_datapath_id(self):
        pass

    @abstractmethod
    def show_ports(self, dpid):
        pass

    @abstractmethod
    def set_outer_port_association_setting(self,
                dpid, outer_port, outer_vlan_id,
                inner_vlan_id, region_name):
        pass

    @abstractmethod
    def clear_outer_port_association_setting(self,
                dpid, outer_port, outer_vlan_id):
        pass

    @abstractmethod
    def save(self):
        pass
