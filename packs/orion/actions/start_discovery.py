# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from lib.actions import OrionBaseAction


class StartDiscovery(OrionBaseAction):
    def run(self,
            name,
            platform,
            poller,
            snmp_communities,
            nodes=None,
            subnets=None,
            ip_ranges=None,
            no_icmp_only=True,
            auto_import=False):
        """
        Create and Start Discovery process in Orion.

        Returns:
         - ProfileID that was created (or error from Orion).
        """
        results = {}

        # Sort out which platform & poller to create the node on.
        if platform is None:
            try:
                platform = self.config['defaults']['platform']
            except IndexError:
                self.send_user_error("No default Orion platform.")
                raise ValueError("No default Orion platform.")

        self.logger.info("Connecting to Orion platform: {}".format(platform))
        self.connect(platform)
        results['platform'] = platform

        # Set BulkList to how Orion likes this to be empty
        BulkList = None
        if nodes is not None:
            BulkList = []
            for node in nodes:
                BulkList.append({'Address': node})

        # Set IpRanges how Orion likes this to be empty
        IpRanges = []
        if ip_ranges is not None:
            for ip_range in ip_ranges:
                (start_ip, end_ip) = ip_range.split(':')
                IpRanges.append({'StartAddress': start_ip,
                                 'EndAddress': end_ip})

        # Set Subnets how Orion likes this to be empty
        Subnets = None
        if subnets is not None:
            Subnets = []
            for subnet in subnets:
                (SubnetIP, SubnetMask) = subnet.split('/')
                Subnets.append({'SubnetIP': SubnetIP,
                                'SubnetMask': SubnetMask})

        CredID_order = 1
        CredIDs = []
        for snmp in snmp_communities:
            CredIDs.append(
                {'CredentialID': self.get_snmp_cred_id(snmp),
                 'Order': CredID_order}
            )
            CredID_order += 1

        CorePluginConfiguration = self.invoke('Orion.Discovery',
                                              'CreateCorePluginConfiguration',
                                              {'BulkList': BulkList,
                                               'IpRanges': IpRanges,
                                               'Subnets': Subnets,
                                               'Credentials': CredIDs,
                                               'WmiRetriesCount': 0,
                                               'WmiRetryIntervalMiliseconds':
                                               1000})

        # engineID if happens to be None, default to the primary (aka 1).
        if poller is not None:
            engineID = self.get_engine_id(poller)
        else:
            engineID = 1

        self.logger.info(
            "Adding '{}' Discovery profile to Orion Platform {}".format(
                name, platform))

        disco = self.invoke('Orion.Discovery', 'StartDiscovery',
                            {
                                'Name': name,
                                'EngineId': engineID,
                                'JobTimeoutSeconds': 3600,
                                'SearchTimeoutMiliseconds': 2000,
                                'SnmpTimeoutMiliseconds': 2000,
                                'SnmpRetries': 4,
                                'RepeatIntervalMiliseconds': 1800,
                                'SnmpPort': 161,
                                'HopCount': 0,
                                'PreferredSnmpVersion': 'SNMP2c',
                                'DisableIcmp': no_icmp_only,
                                'AllowDuplicateNodes': False,
                                'IsAutoImport': auto_import,
                                'IsHidden': False,
                                'PluginConfigurations': [
                                    {'PluginConfigurationItem':
                                     CorePluginConfiguration}
                                ]
                            })

        return disco
