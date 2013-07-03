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

import webob.exc
import netaddr
import re

from keystoneclient.v2_0 import client as keystone_client
from novaclient import extension as nc_ext
from novaclient.v1_1 import client as nova_client
from novaclient.v1_1.contrib import baremetal
from oslo.config import cfg

from quantum.api.v2 import attributes as attr
from quantum.db import api as db
from quantum.db import db_base_plugin_v2
from quantum.db import l3_db
from quantum.db import models_v2
from quantum.extensions import l3
from quantum.openstack.common import jsonutils
from quantum.openstack.common import log
# NOTE (yokose): this import is needed for config init
from quantum.plugins.dodai import config
from quantum.plugins.dodai.db import dodai_db
from quantum.plugins.dodai.db import dodai_models
from quantum.plugins.dodai import exceptions
from quantum.plugins.dodai import ofc_manager


LOG = log.getLogger(__name__)
CONF = cfg.CONF
NOVACLIENT_EXTENSIONS = [
    nc_ext.Extension(baremetal.__name__.split('.')[-1], baremetal),
    ]
DEVICE_OWNER_COMPUTE_PREFIX = 'compute:'
METAKEY_FLOATING_IP_PREFIX = 'floating_ip_'


class DodaiL2EPlugin(db_base_plugin_v2.QuantumDbPluginV2,
                     l3_db.L3_NAT_db_mixin):
    """Dodai Quantum Plugin for a VNC controlled network."""

    # NOTE(yokose): 'router' is needed for '--router:external' option
    supported_extension_aliases = ['router', 'dodai-outer-port']

    def __init__(self):
        attr.RESOURCE_ATTRIBUTE_MAP['networks'].update({
                'vlan_id': {'allow_post': True,
                            'allow_put': True,
                            'validate': {'type:non_negative': None},
                            'required': True,
                            'is_visible': True}})
        # NOTE(yokose): Set the plugin default extension path
        #               if no api_extensions_path is specified.
        if not CONF.api_extensions_path:
            CONF.set_override('api_extensions_path',
                              'quantum/plugins/dodai/extensions')
        db.configure_db()
        self.ofc = ofc_manager.OFCManager()

    def create_network(self, context, network):
        LOG.debug("#DodaiPlugin.create_network() called.")
        LOG.debug("#network=%s" % network)
        session = context.session
        # check vlan id
        vlan_id = network['network']['vlan_id']
        if dodai_db.get_dodai_network_by_vlan_id(session, vlan_id):
            raise exceptions.InvalidVlanId(vlan_id=vlan_id)

        with session.begin(subtransactions=True):
            # create networks
            net = super(DodaiL2EPlugin, self).create_network(context, network)
            # create dodai_networks
            dodai_db.create_dodai_network(session, net['id'], vlan_id)
            # create externalnetworks
            self._process_l3_create(context, network['network'], net['id'])
            self._extend_network_dict_l3(context, net)

        # format response
        net = self._make_dodai_network_dict(net, None, vlan_id)
        LOG.info(_("Network created successfully."))
        return net

    def update_network(self, context, id, network):
        LOG.debug("#DodaiPlugin.update_network() called.")
        LOG.debug("#id=%s" % id)
        LOG.debug("#network=%s" % network)
        session = context.session
        with session.begin(subtransactions=True):
            # update networks
            net = super(DodaiL2EPlugin,
                        self).update_network(context, id, network)
            # NOTE(yokose): updating vlan_id is not allowed.
            # update externalnetworks
            self._process_l3_update(context, network['network'], id)
            self._extend_network_dict_l3(context, net)

        LOG.info(_("Network updated successfully."))
        return self.get_network(context, id)

    def get_network(self, context, id, fields=None):
        query = self._model_query(context, models_v2.Network)
        query = query.join(dodai_models.DodaiNetwork,
                           models_v2.Network.id ==\
                               dodai_models.DodaiNetwork.network_id)
        query = query.add_columns(dodai_models.DodaiNetwork.vlan_id)
        net, vlan_id = query.filter(models_v2.Network.id == id).first()

        # format response
        net[l3.EXTERNAL] = self._network_is_external(context, id)
        net = self._make_dodai_network_dict(net, fields, vlan_id)
        return net

    def get_networks(self, context, filters=None, fields=None,
                     sorts=None, limit=None, marker=None, page_reverse=False):
        query = self._model_query(context, models_v2.Network)
        query = query.join(dodai_models.DodaiNetwork,
                           models_v2.Network.id ==\
                               dodai_models.DodaiNetwork.network_id)
        query = query.add_columns(dodai_models.DodaiNetwork.vlan_id)
        if filters:
            query = self._apply_filters_to_query(query, models_v2.Network,
                                                 filters)
            for key, value in filters.iteritems():
                if key == 'vlan_id':
                    column = dodai_models.DodaiNetwork.vlan_id
                else:
                    column = getattr(models_v2.Network, key, None)
                if column:
                    query = query.filter(column.in_(value))

        # format response
        nets = []
        for net, vlan_id in query.all():
            net[l3.EXTERNAL] = self._network_is_external(context, id)
            net = self._make_dodai_network_dict(net, fields, vlan_id)
            nets.append(net)
        return nets

    def delete_network(self, context, id):
        LOG.debug("#DodaiPlugin.delete_network() called.")
        LOG.debug("#id=%s" % id)
        session = context.session
        with session.begin(subtransactions=True):
            # delete dodai_networks
            dodai_db.delete_dodai_network(session, id)
            # delete networks
            super(DodaiL2EPlugin, self).delete_network(context, id)

        LOG.info(_("Network deleted successfully."))

    def _make_dodai_network_dict(self, network, fields=None, vlan_id=None):
        res = {'id': network['id'],
               'name': network['name'],
               'tenant_id': network['tenant_id'],
               'admin_state_up': network['admin_state_up'],
               'status': network['status'],
               'shared': network['shared'],
               'subnets': [subnet['id']
                           for subnet in network['subnets']],
               l3.EXTERNAL: network[l3.EXTERNAL],
               'vlan_id': vlan_id}

        return self._fields(res, fields)

    def create_port(self, context, port):
        LOG.debug("#DodaiPlugin.create_port() called.")
        LOG.debug("#port=%s" % port)
        device_owner = port['port']['device_owner']
        # NOTE(yokose): If this method is called from run_instance,
        #               device_owner is set as 'compute:None'.
        if device_owner.startswith(DEVICE_OWNER_COMPUTE_PREFIX):
            net_id = port['port']['network_id']
            if self._is_ofc_controlled_network(context, net_id):
                region_name = _uuid_to_region_name(net_id)
                dodai_net = dodai_db.get_dodai_network(context.session, net_id)
                vlan_id = dodai_net['vlan_id']
                try:
                    # create region
                    if not self.ofc.has_region(region_name):
                        self.ofc.create_region(region_name, vlan_id)
                except Exception as e:
                    LOG.error(_("Error occurred in ofc.create_region: %s") % e)
                    raise e

                tenant_id = port['port']['tenant_id']
                device_id = port['port']['device_id']
                mac_address = port['port']['mac_address']
                bm_interface = self._get_bm_interface_by_port(
                                            tenant_id, device_id, mac_address)
                port_no = bm_interface['port_no']
                dpid = bm_interface['datapath_id']
                try:
                    # set server port
                    self.ofc.update_for_run_instance(region_name,
                                                     port_no, dpid)
                except Exception as e:
                    LOG.error(_("Error occurred in "
                                "ofc.update_for_run_instance: %s") % e)
                    raise e

        # create ports
        db_port = super(DodaiL2EPlugin, self).create_port(context, port)
        return db_port

    def delete_port(self, context, id):
        LOG.debug("#DodaiPlugin.delete_port() called.")
        LOG.debug("#id=%s" % id)
        db_port = self._get_port(context, id)
        device_owner = db_port['device_owner']
        # NOTE(yokose): If this method is called from run_instance,
        #               device_owner is set as 'compute:None'.
        if device_owner.startswith(DEVICE_OWNER_COMPUTE_PREFIX):
            net_id = db_port['network_id']
            if self._is_ofc_controlled_network(context, net_id):
                region_name = _uuid_to_region_name(net_id)
                dodai_net = dodai_db.get_dodai_network(context.session, net_id)
                vlan_id = dodai_net['vlan_id']
                tenant_id = db_port['tenant_id']
                device_id = db_port['device_id']
                mac_address = db_port['mac_address']
                bm_interface = self._get_bm_interface_by_port(
                                        tenant_id, device_id, mac_address)
                port_no = bm_interface['port_no']
                dpid = bm_interface['datapath_id']
                try:
                    # clear server port, remove region
                    self.ofc.update_for_terminate_instance(
                                 region_name, port_no, dpid, vlan_id)
                except Exception as e:
                    LOG.error(_("Error occurred in "
                                "ofc.update_for_terminate_instance: %s") % e)
                    raise e

        # set null to floatingips.fixed_port_id, fixed_ip_address
        self.disassociate_floatingips(context, id)
        # delete ports
        super(DodaiL2EPlugin, self).delete_port(context, id)
        LOG.info(_("Port deleted successfully."))

    def update_floatingip(self, context, id, floatingip):
        LOG.debug("#DodaiPlugin.update_floatingip() called.")
        LOG.debug("#id=%s" % id)
        LOG.debug("#floatingip=%s" % floatingip)
        fixed_port_id = floatingip['floatingip']['port_id']
        session = context.session
        # NOTE(yokose): Associate/Disassociate depends on existence of port_id.
        if fixed_port_id:
            # Associate floatingip to instance
            fixed_port = self._get_port(context, fixed_port_id)
            LOG.debug("#fixed_port=%s" % fixed_port)
            tenant_id = fixed_port['tenant_id']
            device_id = fixed_port['device_id']
            LOG.debug("#tenant_id=%s" % tenant_id)
            LOG.debug("#device_id=%s" % device_id)
            if device_id:
                # set instance metadata
                meta_obj = self._create_metadata_object(context, id,
                                                        fixed_port_id)
                self._set_metadata_object_into_floating_ip_metadata(
                             tenant_id, device_id, meta_obj)
            # update floatingips
            fixed_ip_address = floatingip['floatingip'].get('fixed_ip_address')
            db_fip = dodai_db.update_floatingip(session, id,
                                                fixed_ip_address,
                                                fixed_port_id)
        else:
            # Disassociate floatingip from instance
            fip = self._get_floatingip(context, id)
            LOG.debug("#fip=%s" % fip)
            if not fip['fixed_port_id']:
                raise Exception("Port not found.")
            fixed_port_id = fip['fixed_port_id']
            LOG.debug("#fixed_port_id =%s" % fixed_port_id)
            fixed_port = self._get_port(context, fixed_port_id)
            LOG.debug("#fixed_port=%s" % fixed_port)
            tenant_id = fixed_port['tenant_id']
            device_id = fixed_port['device_id']
            LOG.debug("#tenant_id=%s" % tenant_id)
            LOG.debug("#device_id=%s" % device_id)
            if device_id:
                # delete instance metadata
                floating_ip_address = fip['floating_ip_address']
                self._delete_metadata_object_into_floating_ip_metadata(
                             tenant_id, device_id, floating_ip_address)
            # update floatingips
            db_fip = dodai_db.update_floatingip(session, id, None, None)

        LOG.info(_("Floating IP updated successfully."))
        return self._make_floatingip_dict(db_fip)

    def delete_floatingip(self, context, id):
        LOG.debug("#DodaiPlugin.delete_floatingip() called.")
        LOG.debug("#id=%s" % id)
        floatingip = self._get_floatingip(context, id)
        session = context.session
        with session.begin(subtransactions=True):
            # delete floatingips
            dodai_db.delete_floatingip(session, id)
            # delete ports(floating ip port)
            self.delete_port(context.elevated(),
                             floatingip['floating_port_id'])
        LOG.info(_("Floating IP deleted successfully."))

    def _get_nova_client(self, tenant_id):
        kc = keystone_client.Client(username=CONF.KEYSTONE.username,
                                    password=CONF.KEYSTONE.password,
                                    tenant_id=tenant_id,
                                    auth_url=CONF.KEYSTONE.auth_url)
        tenant = kc.tenants.get(tenant_id)
        tenant_name = tenant.name

        nc = nova_client.Client(CONF.KEYSTONE.username,
                                CONF.KEYSTONE.password,
                                tenant_name,
                                CONF.KEYSTONE.auth_url,
                                extensions=NOVACLIENT_EXTENSIONS,
                                no_cache=True)
        return nc

    def _get_instance_by_uuid(self, tenant_id, uuid):
        nc = self._get_nova_client(tenant_id)
        instance = nc.servers.get(uuid)
        return instance

    def _get_bm_node_by_uuid(self, tenant_id, uuid):
        nc = self._get_nova_client(tenant_id)
        bm_nodes = [n for n in nc.baremetal.list() if n.uuid == uuid]
        if not bm_nodes:
            return None
        return bm_nodes[0]

    def _get_bm_interface_by_port(self, tenant_id, device_id, mac_address):
        instance = self._get_instance_by_uuid(tenant_id, device_id)
        if not instance:
            LOG.warning(_("Error occurred:"))
            raise Exception("plugin raised exception, check logs")
        node_uuid = instance.__getattr__('OS-EXT-SRV-ATTR:hypervisor_hostname')
        bm_node = self._get_bm_node_by_uuid(tenant_id, node_uuid)
        if not bm_node:
            LOG.warning(_("Error occurred:"))
            raise Exception("plugin raised exception, check logs")
        for bm_interface in bm_node.interfaces:
            if mac_address == bm_interface['address']:
                LOG.debug("#bm_interface=%s" % bm_interface)
                return bm_interface
        else:
            LOG.warning(_("Error occurred. bm_interface does not exist."))
            raise Exception("plugin raised exception, check logs")

    def _get_subnet_from_floating_ip(self, context, fip):
        # NOTE(yokose): identify subnet by floatingip-ipallocation relationship
        session = context.session
        ipallocation = dodai_db.get_ipallocation_by_floatingip(session,
                                   fip['floating_port_id'],
                                   fip['floating_ip_address'],
                                   fip['floating_network_id'])
        subnet = self._get_subnet(context, ipallocation['subnet_id'])
        return subnet

    def _set_metadata_object_into_floating_ip_metadata(self, tenant_id,
                                                       instance_uuid,
                                                       new_meta_obj):
        floating_ip_metadata = self._get_floating_ip_metadata(tenant_id,
                                                              instance_uuid)
        max_num = 0
        for key, value in floating_ip_metadata.iteritems():
            LOG.debug("#key=%s" % key)
            LOG.debug("#value=%s" % value)
            match = re.match('^' + METAKEY_FLOATING_IP_PREFIX + '(\d+)$', key)
            if match is not None:
                num = int(match.group(1))
                meta_obj = jsonutils.loads(value)
                LOG.debug("#num=%s" % str(num))
                LOG.debug("#new_meta_obj=%s" % new_meta_obj)
                LOG.debug("#meta_obj=%s" % meta_obj)
                if new_meta_obj['ip_address'] == meta_obj['ip_address']:
                    self._set_instance_metadata(tenant_id, instance_uuid,
                                    key, jsonutils.dumps(new_meta_obj))
                    return
                if max_num < num:
                    max_num = num
        else:
            LOG.debug("#max_num=%s" % str(max_num))
            self._set_instance_metadata(tenant_id, instance_uuid,
                         METAKEY_FLOATING_IP_PREFIX + unicode(max_num + 1),
                         jsonutils.dumps(new_meta_obj))

    def _delete_metadata_object_into_floating_ip_metadata(self, tenant_id,
                                                          instance_uuid,
                                                          floating_ip_address):
        floating_ip_metadata = self._get_floating_ip_metadata(tenant_id,
                                                              instance_uuid)
        for key, value in floating_ip_metadata.iteritems():
            match = re.match('^' + METAKEY_FLOATING_IP_PREFIX + '(\d+)$', key)
            if match is not None:
                meta_obj = jsonutils.loads(value)
                if floating_ip_address == meta_obj['ip_address']:
                    LOG.debug("Tring to delete metadata from instance.")
                    LOG.debug("#tenant_id=%s" % tenant_id)
                    LOG.debug("#instance_uuid=%s" % instance_uuid)
                    LOG.debug("#key=%s" % key)
                    self._delete_instance_metadata(tenant_id,
                                                   instance_uuid, key)
                    return
        else:
            LOG.warn("Instance metadata has already been deleted.")

    def _create_metadata_object(self, context, floatingip_id, fixed_port_id):
        fixed_port = self._get_port(context, fixed_port_id)
        LOG.debug("#fixed_port=%s" % fixed_port)
        tenant_id = fixed_port['tenant_id']
        device_id = fixed_port['device_id']
        LOG.debug("#tenant_id=%s" % tenant_id)
        LOG.debug("#device_id=%s" % device_id)
        fip = self._get_floatingip(context, floatingip_id)
        floating_ip_address = fip['floating_ip_address']
        floating_port = self._get_port(context, fip['floating_port_id'])
        subnet = self._get_subnet_from_floating_ip(context, fip)
        dnss = [{'address': dnsnameserver['address']} for dnsnameserver
                     in self._get_dns_by_subnet(context, subnet['id'])]
        meta_obj = {'ip_address': floating_ip_address,
                    'mac_address': floating_port['mac_address'],
                    'netmask': _cidr_to_netmask(subnet['cidr']),
                    'gateway_ip': subnet['gateway_ip'],
                    'dnsnameservers': dnss}
        return meta_obj

    def _get_floating_ip_metadata(self, tenant_id, instance_uuid):
        metadata = self._get_instance_metadata(tenant_id, instance_uuid)
        floating_ip_metadata = {}
        for key, value in metadata.iteritems():
            match = re.match('^' + METAKEY_FLOATING_IP_PREFIX + '(\d+)$', key)
            if match is not None:
                floating_ip_metadata.update({key: value})
        return floating_ip_metadata

    def _get_instance_metadata(self, tenant_id, instance_uuid):
        nc = self._get_nova_client(tenant_id)
        result = nc.servers.get(instance_uuid)
        return result.metadata

    def _set_instance_metadata(self, tenant_id, instance_uuid, key, value):
        nc = self._get_nova_client(tenant_id)
        result = nc.servers.set_meta(instance_uuid, {key: value})
        return result

    def _delete_instance_metadata(self, tenant_id, instance_uuid, key):
        nc = self._get_nova_client(tenant_id)
        nc.servers.delete_meta(instance_uuid, [key])

    def _is_ofc_controlled_network(self, context, network_id):
        # NOTE(yokose): Whether send request to OFC or not depends on
        #               the name of network.
        net = self._get_network(context, network_id)
        return net['name'] not in CONF.OFC.ofc_uncontrolled_network_names

    """
    Not supported API
    """
    def create_router(self, context, router):
        raise webob.exc.HTTPNotFound("The resource could not be found.")

    def update_router(self, context, id, router):
        raise webob.exc.HTTPNotFound("The resource could not be found.")

    def delete_router(self, context, id):
        raise webob.exc.HTTPNotFound("The resource could not be found.")

    def get_router(self, context, id, fields=None):
        raise webob.exc.HTTPNotFound("The resource could not be found.")

    def get_routers(self, context, filters=None, fields=None,
                    sorts=None, limit=None, marker=None,
                    page_reverse=False):
        raise webob.exc.HTTPNotFound("The resource could not be found.")

    def get_routers_count(self, context, filters=None):
        raise webob.exc.HTTPNotFound("The resource could not be found.")

    def add_router_interface(self, context, router_id, interface_info):
        raise webob.exc.HTTPNotFound("The resource could not be found.")

    def remove_router_interface(self, context, router_id, interface_info):
        raise webob.exc.HTTPNotFound("The resource could not be found.")


def _uuid_to_region_name(uuid):
    if uuid is None:
        return uuid
    return uuid.replace('-', '')


def _cidr_to_netmask(cidr):
    if cidr is None:
        return None
    return str(netaddr.IPNetwork(cidr).netmask)
