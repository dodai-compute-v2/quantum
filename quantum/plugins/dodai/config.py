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

from oslo.config import cfg


ofc_opts = [
    cfg.StrOpt('ofc_driver',
               default='quantum.plugins.dodai.drivers.l2e_vnc.'
                       'DodaiL2EVNCV2Driver',
               help='The driver used to manage the OpenFlow Controller.'),
    cfg.StrOpt('ofc_service_url',
               default=None,
               help='URL of open flow controller service.'),
    cfg.ListOpt('ofc_uncontrolled_network_names',
                default=[],
                help="The name list of the networks that have no need to send "
                     "requests to OFC."),
]

nova_opts = [
    cfg.StrOpt('username', help=_("Nova admin user")),
    cfg.StrOpt('password', help=_("Nova admin password"),
               secret=True),
    cfg.StrOpt('tenant_name', help=_("Nova admin tenant name")),
    cfg.StrOpt('auth_url', help=_("Authentication URL")),
]

CONF = cfg.CONF
CONF.register_opts(ofc_opts, 'OFC')
CONF.register_opts(nova_opts, 'NOVA')
