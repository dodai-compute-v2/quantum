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

import logging
from suds.client import Client

from oslo.config import cfg

from quantum.openstack.common import log
from quantum.plugins.dodai.drivers import ofc_driver_base


logging.getLogger('suds').setLevel(logging.INFO)
LOG = log.getLogger(__name__)
CONF = cfg.CONF


def get_client():
    client = Client(CONF.OFC.ofc_service_url + "?wsdl")
    return client


class DodaiL2EVNCV2Driver(ofc_driver_base.OFCDriverBase):
    """OFC Driver for L2E-VNC2.0"""

    def __init__(self):
        pass

    def create_region(self, region_name):
        LOG.debug("#DodaiL2EVNCV2Driver.create_region() called.")
        LOG.debug("#region_name=%s" % region_name)
        client = get_client()
        response = client.service.createRegion(region_name)
        LOG.debug("#DodaiL2EVNCV2Driver.create_region() response is (%s)" %
                  response)

    def destroy_region(self, region_name):
        LOG.debug("#DodaiL2EVNCV2Driver.destroy_region() called.")
        LOG.debug("#region_name=%s" % region_name)
        client = get_client()
        response = client.service.destroyRegion(region_name)
        LOG.debug("#DodaiL2EVNCV2Driver.destroy_region() response is (%s)" %
                  response)

    def show_region(self):
        LOG.debug("#DodaiL2EVNCV2Driver.show_region() called.")
        client = get_client()
        return client.service.showRegion()

    def set_server_port(self, dpid, server_port, region_name):
        LOG.debug("#DodaiL2EVNCV2Driver.set_server_port() called.")
        LOG.debug("#dpid=%s" % dpid)
        LOG.debug("#server_port=%s" % server_port)
        LOG.debug("#region_name=%s" % region_name)
        client = get_client()
        response = client.service.setServerPort(dpid, server_port, region_name)
        LOG.debug("#DodaiL2EVNCV2Driver.set_server_port() response is (%s)" %
                  response)

    def clear_server_port(self, dpid, server_port):
        LOG.debug("#DodaiL2EVNCV2Driver.clear_server_port() called.")
        LOG.debug("#dpid=%s" % dpid)
        LOG.debug("#server_port=%s" % server_port)
        client = get_client()
        response = client.service.clearServerPort(dpid, server_port)
        LOG.debug("#DodaiL2EVNCV2Driver.clear_server_port() response is (%s)"
                  % response)

    def show_switch_datapath_id(self):
        LOG.debug("#DodaiL2EVNCV2Driver.show_switch_datapath_id() called.")
        client = get_client()
        return client.service.showDatapathId()

    def show_ports(self, dpid):
        LOG.debug("#DodaiL2EVNCV2Driver.show_ports() called.")
        LOG.debug("#dpid=%s" % dpid)
        client = get_client()
        return client.service.showPorts(dpid)

    def set_outer_port_association_setting(self,
                dpid, outer_port, outer_vlan_id,
                inner_vlan_id, region_name):
        LOG.debug("#DodaiL2EVNCV2Driver.set_outer_port_association_setting() "
                  "called.")
        LOG.debug("#dpid=%s" % dpid)
        LOG.debug("#outer_port=%s" % outer_port)
        LOG.debug("#outer_vlan_id=%s" % outer_vlan_id)
        LOG.debug("#inner_vlan_id=%s" % inner_vlan_id)
        LOG.debug("#region_name=%s" % region_name)
        client = get_client()
        response = client.service.setOuterPortAssociationSetting(
            dpid, outer_port, outer_vlan_id,
            inner_vlan_id, region_name)
        LOG.debug("#DodaiL2EVNCV2Driver.set_outer_port_association_setting() "
                  "response is (%s)" % response)

    def clear_outer_port_association_setting(self,
                dpid, outer_port, outer_vlan_id):
        LOG.debug("#DodaiL2EVNCV2Driver."
                  "clear_outer_port_association_setting() called.")
        LOG.debug("#dpid=%s" % dpid)
        LOG.debug("#outer_port=%s" % outer_port)
        LOG.debug("#outer_vlan_id=%s" % outer_vlan_id)
        client = get_client()
        response = client.service.clearOuterPortAssociationSetting(
            dpid, outer_port, outer_vlan_id)
        LOG.debug("#DodaiL2EVNCV2Driver."
                  "clear_outer_port_association_setting() response is (%s)" %
                  response)

    def save(self):
        LOG.debug("#DodaiL2EVNCV2Driver.save() called.")
        client = get_client()
        response = client.service.save()
        LOG.debug("#DodaiL2EVNCV2Driver.save() reponse is (%s)" % response)


class VNCDummyDriver(ofc_driver_base.OFCDriverBase):
    """DummyDriver for VNC"""

    def __init__(self):
        LOG.debug("#VNCDummyDriver.__init__() called.")

    def create_region(self, region_name):
        LOG.debug("#VNCDummyDriver.create_region() called.")
        LOG.debug("#region_name=%s" % region_name)

    def destroy_region(self, region_name):
        LOG.debug("#VNCDummyDriver..destroy_region() called.")
        LOG.debug("#region_name=%s" % region_name)

    def show_region(self):
        LOG.debug("#VNCDummyDriver.show_region() called.")
        return []

    def set_server_port(self, dpid, server_port, region_name):
        LOG.debug("#VNCDummyDriver.set_server_port() called.")
        LOG.debug("#dpid=%s" % dpid)
        LOG.debug("#server_port=%s" % server_port)
        LOG.debug("#region_name=%s" % region_name)

    def clear_server_port(self, dpid, server_port):
        LOG.debug("#VNCDummyDriver.clear_server_port() called.")
        LOG.debug("#dpid=%s" % dpid)
        LOG.debug("#server_port=%s" % server_port)

    def show_switch_datapath_id(self):
        LOG.debug("#VNCDummyDriver.show_switch_datapath_id() called.")
        return []

    def show_ports(self, dpid):
        LOG.debug("#VNCDummyDriver.show_ports() called.")
        LOG.debug("#dpid=%s" % dpid)
        return []

    def set_outer_port_association_setting(self,
                dpid, outer_port, outer_vlan_id,
                inner_vlan_id, region_name):
        LOG.debug("#VNCDummyDriver.set_outer_port_association_setting()"\
                  " called.")
        LOG.debug("#dpid=%s" % dpid)
        LOG.debug("#outer_port=%s" % outer_port)
        LOG.debug("#outer_vlan_id=%s" % outer_vlan_id)
        LOG.debug("#inner_vlan_id=%s" % inner_vlan_id)
        LOG.debug("#region_name=%s" % region_name)

    def clear_outer_port_association_setting(self,
                dpid, outer_port, outer_vlan_id):
        LOG.debug("#VNCDummyDriver.clear_outer_port_association_setting()"\
                  " called.")
        LOG.debug("#dpid=%s" % dpid)
        LOG.debug("#outer_port=%s" % outer_port)
        LOG.debug("#outer_vlan_id=%s" % outer_vlan_id)

    def save(self):
        LOG.debug("#VNCDummyDriver.save() called.")
