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

# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging
import webob.exc
from abc import abstractmethod

from quantum.api import api_common as common
from quantum.api import extensions
from quantum.api.v2 import attributes as attr
from quantum.common import exceptions as q_exc
from quantum.plugins.dodai import exceptions as d_exc
from quantum.plugins.dodai.db import dodai_db
from quantum import manager
from quantum import policy
from quantum import wsgi


LOG = logging.getLogger(__name__)

# Attribute Map
RESOURCE_NAME = 'dodai-outer-port'
COLLECTION_NAME = '%ss' % RESOURCE_NAME
EXT_ALIAS = RESOURCE_NAME

RESOURCE_ATTRIBUTE_MAP = {
    COLLECTION_NAME: {
        'id': {'allow_post': False, 'allow_put': False,
               'is_visible': True},
        'dpid': {'allow_post': True, 'allow_put': False,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': False},
        'outer_port': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:string': None},
                       'is_visible': True, 'default': ''},
    },
}


class Dodai_outer_port(extensions.ExtensionDescriptor):
    """Dodai OuterPort extension"""

    @classmethod
    def get_name(cls):
        return "Quantum Dodai OuterPort Management"

    @classmethod
    def get_alias(cls):
        return EXT_ALIAS

    @classmethod
    def get_description(cls):
        return _("API for retrieving and managing Dodai OuterPort for "
                 "Quantum advanced services")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/dodai-outer-port/api/v2.0"

    @classmethod
    def get_updated(cls):
        return "2013-10-01T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """ Returns Ext Resources """
        my_plurals = [(key, key[:-1]) for key in RESOURCE_ATTRIBUTE_MAP.keys()]
        attr.PLURALS.update(dict(my_plurals))
        plugin = manager.QuantumManager.get_plugin()
        return [extensions.ResourceExtension(
                    COLLECTION_NAME,
                    DodaiOuterPortController(plugin),
                    attr_map=RESOURCE_ATTRIBUTE_MAP[COLLECTION_NAME])]


class DodaiOuterPortController(common.QuantumController, wsgi.Controller):
    """ Dodai OuterPort API controller
        based on QuantumController """

    _dodai_outer_port_ops_param_list = [
        {'param-name': 'dpid', 'required': True},
        {'param-name': 'outer_port', 'required': True},
    ]

    def __init__(self, plugin):
        self._resource_name = RESOURCE_NAME.replace('-', '_')
        self._plugin = plugin

    def index(self, request):
        """ Returns a list of Dodai OuterPorts """
        policy.enforce(request.context, "outer-port-list", {})
        dops = dodai_db.get_all_dodai_outer_ports(None)
        result = [self._make_dodai_outer_port_dict(dop)[self._resource_name]
                      for dop in dops]
        return dict(dodai_outer_ports=result)

    def show(self, request, id):
        """ Returns Dodai OuterPort details for the given id """
        policy.enforce(request.context, "outer-port-show", {})
        dop = dodai_db.get_dodai_outer_port(None, id)
        if dop is None:
            msg = (_("Unable to find %s with the specified identifier.") %
                   self._resource_name)
            LOG.error(msg)
            return webob.Response(status=404, body=msg)
        return self._make_dodai_outer_port_dict(dop)

    def create(self, request):
        """ Creates a new Dodai OuterPort """
        policy.enforce(request.context, "outer-port-create", {})
        try:
            body = self._deserialize(request.body, request.get_content_type())
            req_body = self._prepare_request_body(body,
                                self._dodai_outer_port_ops_param_list)
            req_params = req_body[self._resource_name]
        except webob.exc.HTTPError as e:
            return webob.Response(status=400, body=str(e))
        dop = dodai_db.create_dodai_outer_port(None,
                                               req_params['dpid'],
                                               req_params['outer_port'])
        return self._make_dodai_outer_port_dict(dop)

    def delete(self, request, id):
        """ Destroys the Dodai OuterPort with the given id """
        policy.enforce(request.context, "outer-port-delete", {})
        dop = dodai_db.get_dodai_outer_port(None, id)
        if dop is None:
            msg = (_("Unable to find %s with the specified identifier.") %
                   self._resource_name)
            LOG.error(msg)
            return webob.Response(status=404, body=msg)
        dodai_db.delete_dodai_outer_port(None, id)

    def _make_dodai_outer_port_dict(self, dop):
        return dict(dodai_outer_port=dict(
                        id=dop['id'],
                        dpid=dop['dpid'],
                        outer_port=dop['outer_port']))
