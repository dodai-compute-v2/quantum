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

from sqlalchemy.orm import exc

from oslo.config import cfg

from quantum.common import exceptions as q_exc
from quantum.db import api as db
from quantum.db import l3_db
from quantum.db import models_v2
from quantum.openstack.common import log
from quantum.plugins.dodai.db import dodai_models
from quantum.plugins.dodai import exceptions as d_exc


LOG = log.getLogger(__name__)


def initialize():
    db.configure_db()


def create_dodai_network(session, network_id, vlan_id):
    if not session:
        session = db.get_session()
    with session.begin(subtransactions=True):
        dodai_net = dodai_models.DodaiNetwork(network_id, vlan_id)
        session.add(dodai_net)
    return dodai_net


def delete_dodai_network(session, network_id):
    if not session:
        session = db.get_session()
    with session.begin(subtransactions=True):
        dodai_net = get_dodai_network(session, network_id)
        if dodai_net is not None:
            session.delete(dodai_net)


def get_dodai_network(session, network_id):
    if not session:
        session = db.get_session()
    dodai_net = (session.query(dodai_models.DodaiNetwork).
                 filter_by(network_id=network_id).
                 first())
    return dodai_net


def get_dodai_network_by_vlan_id(session, vlan_id):
    if not session:
        session = db.get_session()
    dodai_net = (session.query(dodai_models.DodaiNetwork).
                 filter_by(vlan_id=vlan_id).
                 first())
    return dodai_net


def update_floatingip(session, id, fixed_ip_address, fixed_port_id):
    if not session:
        session = db.get_session()
    with session.begin(subtransactions=True):
        floatingip = (session.query(l3_db.FloatingIP).
                      filter_by(id=id).
                      first())
        floatingip.update({'fixed_ip_address': fixed_ip_address,
                           'fixed_port_id': fixed_port_id})
    return floatingip


def delete_floatingip(session, id):
    if not session:
        session = db.get_session()
    with session.begin(subtransactions=True):
        floatingip = (session.query(l3_db.FloatingIP).
                      filter_by(id=id).
                      first())
        session.delete(floatingip)


def get_ipallocation_by_floatingip(session, port_id, ip_address, network_id):
    if not session:
        session = db.get_session()
    ipallocation = (session.query(models_v2.IPAllocation).
                    filter_by(port_id=port_id).
                    filter_by(ip_address=ip_address).
                    filter_by(network_id=network_id).
                    first())
    return ipallocation


def create_dodai_outer_port(session, dpid, outer_port):
    """
    Creates dodai_outer_port record.
    """
    if not session:
        session = db.get_session()
    with session.begin(subtransactions=True):
        dodai_outer_port = dodai_models.DodaiOuterPort(dpid, outer_port)
        session.add(dodai_outer_port)
    return dodai_outer_port


def delete_dodai_outer_port(session, id):
    """
    Deletes dodai_outer_port record.
    """
    if not session:
        session = db.get_session()
    with session.begin(subtransactions=True):
        dodai_outer_port = get_dodai_outer_port(session, id)
        if dodai_outer_port is not None:
            session.delete(dodai_outer_port)


def get_dodai_outer_port(session, id):
    """
    Get a dodai_outer_port record by id.
    """
    if not session:
        session = db.get_session()
    dodai_outer_port = (session.query(dodai_models.DodaiOuterPort).
                        filter_by(id=id).
                        first())
    return dodai_outer_port


def get_all_dodai_outer_ports(session):
    """
    Get all dodai_outer_port records.
    """
    if not session:
        session = db.get_session()
    return (session.query(dodai_models.DodaiOuterPort).
                          all())
