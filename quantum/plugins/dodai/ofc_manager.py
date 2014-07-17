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

from oslo.config import cfg

from quantum.openstack.common import importutils
from quantum.plugins.dodai import exceptions
from quantum.plugins.dodai.db import dodai_db


logging.getLogger('suds').setLevel(logging.INFO)

CONF = cfg.CONF


class OFCManager():
    """This class manages an OpenFlow Controller"""

    def __init__(self):
        self.ofc_driver = importutils.import_object(CONF.OFC.ofc_driver)

    def update_for_run_instance(self, region_name, server_port, dpid):
        self.ofc_driver.set_server_port(dpid, server_port, region_name)
        self.ofc_driver.save()

    def update_for_terminate_instance(self, region_name, server_port, dpid,
                                      vlan_id):
        self.ofc_driver.clear_server_port(dpid, server_port)
        self.ofc_driver.save()

        dpid_datas = self.ofc_driver.show_switch_datapath_id()
        for dpid_data in dpid_datas:
            ports = self.ofc_driver.show_ports(dpid_data.dpid)
            for port in ports:
                if port.type != 'ServerPort':
                    continue

                if port.regionName == region_name:
                    return

    def create_region(self, region_name, vlan_id):
        try:
            self.ofc_driver.create_region(region_name)
            self.ofc_driver.save()
        except:
            raise exceptions.OFCRegionCreationFailed(region_name=region_name)

        # NOTE(yokose): If vlan is not specified,
        #               set_outer_port_association_setting is skipped
        if vlan_id:
            try:
                dodai_outer_ports = dodai_db.get_all_dodai_outer_ports(None)
                for dodai_outer_port in dodai_outer_ports:
                    self.ofc_driver.set_outer_port_association_setting(
                            dodai_outer_port['dpid'],
                            dodai_outer_port['outer_port'],
                            vlan_id, 65535, region_name)

                self.ofc_driver.save()
            except:
                self.ofc_driver.destroy_region(region_name)
                self.ofc_driver.save()
                raise exceptions.OFCRegionSettingOuterPortAssocFailed(
                                region_name=region_name, vlan_id=vlan_id)

    def remove_region(self, region_name, vlan_id):
        # NOTE(yokose): If vlan is not specified,
        #               clear_outer_port_association_setting is skipped
        if vlan_id:
            try:
                dodai_outer_ports = dodai_db.get_all_dodai_outer_ports(None)
                for dodai_outer_port in dodai_outer_ports:
                    self.ofc_driver.clear_outer_port_association_setting(
                            dodai_outer_port['dpid'],
                            dodai_outer_port['outer_port'],
                            vlan_id)

                self.ofc_driver.save()
            except:
                pass

        self.ofc_driver.destroy_region(region_name)
        self.ofc_driver.save()

    def has_region(self, region_name):
        return region_name in [x.regionName for x
                               in self.ofc_driver.show_region()]
