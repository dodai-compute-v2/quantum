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

from quantum.common import exceptions as q_exc


class InvalidVlanId(q_exc.Conflict):
    message = _("Unable to create the network. "
                "Network with the same vlan_id %(vlan_id)s already exists.")


class DodaiPluginException(q_exc.QuantumException):
    message = _("Error occurred in %s")


class DodaiOuterPortNotFound(q_exc.QuantumException):
    """Dodai OuterPort with this ID cannot be found"""
    message = _("Dodai OuterPort %(id)s could not be found.")


class OFCRegionNotFound(q_exc.QuantumException):
    message = _("Region %(region_name)s of open flow controller "
                "could not be found.")


class OFCRegionExisted(q_exc.QuantumException):
    message = _("Region %(region_name)s of open flow controller has existed.")


class OFCRegionCreationFailed(q_exc.QuantumException):
    message = _("It failed to create region %(region_name)s.")


class OFCRegionSettingOuterPortAssocFailed(q_exc.QuantumException):
    message = _("It failed set outer port association for region "
                "%(region_name)s and vlan id %(vlan_id)s.")
