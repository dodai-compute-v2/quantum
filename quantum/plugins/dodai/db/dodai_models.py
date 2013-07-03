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

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from quantum.db import models_v2
from quantum.db.models_v2 import model_base


class DodaiNetwork(model_base.BASEV2):
    __tablename__ = 'dodai_networks'

    network_id = Column(String(36), nullable=False, primary_key=True)
    vlan_id = Column(Integer)

    def __init__(self, network_id, vlan_id):
        self.network_id = network_id
        self.vlan_id = vlan_id

    def __repr__(self):
        return "<DodaiNetwork(%s, %d)>" % (self.network_id,
                                           self.vlan_id)


class DodaiOuterPort(model_base.BASEV2):
    __tablename__ = 'dodai_outer_ports'

    id = Column(Integer, nullable=False, primary_key=True)
    dpid = Column(String(255))
    outer_port = Column(Integer)

    def __init__(self, dpid, outer_port):
        self.dpid = dpid
        self.outer_port = outer_port

    def __repr__(self):
        return "<DodaiOuterPort(%d, %s, %d)>" % (self.id, self.dpid,
                                                 self.outer_port)
