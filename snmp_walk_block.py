from enum import Enum
from pysnmp.entity.rfc3413.oneliner import cmdgen
from nio.common.discovery import Discoverable, DiscoverableType
from nio.metadata.properties import SelectProperty, StringProperty
from .snmp_base_block import SNMPBase


class SNMPType(Enum):
    SMIv1 = 0
    SMIv2 = 1


@Discoverable(DiscoverableType.block)
class SNMPWalk(SNMPBase):

    """ SNMP block supporting SNMP v1 and v2

    """
    community = StringProperty(title="Community", default='public')
    snmp_version = SelectProperty(SNMPType, title="SNMP version",
                                  default=SNMPType.SMIv2)

    def _create_data(self):
        """ SNMP v1 and v2 use CommunityData
        """
        return cmdgen.CommunityData(
            self.community, mpModel=self.snmp_version.value)

    def _execute_snmp_request(self, oids):
        return self._cmdGen.nextCmd(
            self._data,
            self._transport,
            *oids,
            lookupNames=self.lookup_names,
            lookupValues=self.lookup_values)

    def _handle_data(self, var_binds, starting_signal):
        """ Notify signals in the "default" output """

        for result in var_binds:
            for inner_tuple in result:
                self._enrich_signal(starting_signal, inner_tuple)

        self.notify_signals([starting_signal])