"""

  SNMP Block

"""
from enum import Enum
from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.common.signal.base import Signal
from nio.metadata.properties import TimeDeltaProperty, BoolProperty, \
    SelectProperty
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.string import StringProperty
from nio.modules.scheduler import Job
from pysnmp.entity.rfc3413.oneliner import cmdgen


class BaseSNMPBlock(Block):

    """ A base block implementing a SNMP Manager

    Request SNMP GET ops to SNMP Agents for retrieving monitor data and
    publish them as signals
    """

    agent_host = StringProperty(title="SNMP Agent Url", default='127.0.0.1')
    agent_port = IntProperty(title="SNMP Agent Port", default=161)
    oids = StringProperty(title="List of OIDs")
    pool_interval = TimeDeltaProperty(
        title='Pooling interval', default={"seconds": 10})
    timeout = TimeDeltaProperty(title='SNMP GET Timeout',
                                default={"seconds": 1})
    retries = IntProperty(title="SNMP GET Retries", default=5)
    lookup_names = BoolProperty(title="Look up OId names", default=False)
    lookup_values = BoolProperty(title="Look up OId values", default=False)

    def __init__(self):
        super().__init__()
        self._cmdGen = cmdgen.CommandGenerator()
        self._data = None
        self._transport = None
        self._job = None

    def _request_GET(self):
        oids = self.oids.split(',')
        errorIndication, errorStatus, errorIndex, varBinds = \
            self._cmdGen.getCmd(self._data,
                                self._transport,
                                *oids,
                                lookupNames=self.lookup_names,
                                lookupValues=self.lookup_values)

        # Check for errors and print out results
        if errorIndication:
            self._logger.error("SNMP GET Error: %s" % errorIndication)
            self.notify_signals([Signal({"error": errorIndication})])
        else:
            if errorStatus:
                error = ('%s at %s' % (
                    errorStatus.prettyPrint(),
                    errorIndex and varBinds[int(errorIndex)-1][0] or '?'
                    )
                )
                self._logger.error("SNMP GET Error: %s" % error)
                self.notify_signals([Signal({"error": error})])
            else:
                # TODO, Add check for DEBUG flag
                signal = {}
                for name, val in varBinds:
                    signal[name.prettyPrint()] = val.prettyPrint()
                self.notify_signals([Signal(signal)])

    def configure(self, context):
        super().configure(context)
        self._data = self._create_data()
        self._transport = cmdgen.UdpTransportTarget(
            (self.agent_host, self.agent_port),
            timeout=self.timeout.seconds,
            retries=self.retries)

    def start(self):
        super().start()
        self._job = Job(self._request_GET, self.pool_interval, True)
        self._logger.info("SNMP Manager polling started")

    def stop(self):
        if self._job:
            self._job.cancel()
            self._job = None
        self._logger.info("SNMP Manager polling stopped")
        super().stop()


class SNMPType(Enum):
    SMIv1 = 0
    SMIv2 = 1


@Discoverable(DiscoverableType.block)
class SNMPBlock(BaseSNMPBlock):
    """ SNMP block supporting SNMP v1 and v2

    """
    community = StringProperty(title="Community", default='public')
    snmp_version = SelectProperty(SNMPType, title="SNMP version",
                                  default=SNMPType.SMIv2)

    def _create_data(self):
        return cmdgen.CommunityData(self.community,
                                    mpModel=self.snmp_version.value)