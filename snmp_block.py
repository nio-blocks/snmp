"""
::::::::::::::::::::::::::
  NOTE

  This block file is deprecated - edit the base block file to make changes

::::::::::::::::::::::::::
"""
from enum import Enum
from nio.common.block.attribute import Output
from nio.common.block.base import Block
from nio.common.discovery import Discoverable, DiscoverableType
from nio.common.signal.base import Signal
from nio.common.signal.status import StatusSignal, SignalStatus
from nio.metadata.properties import TimeDeltaProperty, BoolProperty, \
    SelectProperty, ListProperty
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.version import VersionProperty
from nio.modules.scheduler import Job
from pysnmp.entity.rfc3413.oneliner import cmdgen


@Output("status")
class BaseSNMPBlock(Block):

    """ A base block implementing a SNMP Manager

    Request SNMP GET ops to SNMP Agents for retrieving monitor data and
    publish them as signals
    """

    agent_host = StringProperty(title="SNMP Agent Url", default='127.0.0.1')
    agent_port = IntProperty(title="SNMP Agent Port", default=161)
    pool_interval = TimeDeltaProperty(
        title='Pooling interval', default={"seconds": 10})
    timeout = TimeDeltaProperty(title='SNMP GET Timeout',
                                default={"seconds": 1})
    retries = IntProperty(title="SNMP GET Retries", default=5)
    lookup_names = BoolProperty(title="Look up OId names", default=False)
    lookup_values = BoolProperty(title="Look up OId values", default=False)
    oids = ListProperty(str, title="List of OID")
    version = VersionProperty('0.1.0')

    def __init__(self):
        super().__init__()
        self._cmdGen = cmdgen.CommandGenerator()
        self._data = None
        self._transport = None
        self._job = None

    def _create_data(self):
        """ Method to be override in inherited classes
          Returns the data required by cmdGen for executing SNMP GET
          operations on an Agent
        """
        raise NotImplementedError()

    def _request_GET(self):
        """ Executes SNMP GET request
        """
        errorIndication, errorStatus, errorIndex, varBinds = \
            self._cmdGen.getCmd(self._data,
                                self._transport,
                                *self.oids,
                                lookupNames=self.lookup_names,
                                lookupValues=self.lookup_values)

        # Check for errors
        if errorIndication:
            self._handle_error(errorIndication)
        else:
            # Agent report Error Status ?
            if errorStatus:
                self._handle_error_status(errorStatus, errorIndex, varBinds)
            else:
                self._handle_data(varBinds, Signal())

    def _handle_error(self, error):
        """ Handles errors that put the block in a "Error" status
        """
        self._logger.error("SNMP GET Error: %s" % error)
        self.notify_management_signal(StatusSignal(SignalStatus.error, error))

    def _handle_error_status(self, errorStatus, errorIndex, varBinds):
        """ Handles status errors that put the block in a "Warning" status
        and notifies in "status" output
        """
        error = ('%s at %s' % (
            errorStatus.prettyPrint(),
            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'
        )
        )
        self._logger.error("SNMP GET Error: %s" % error)
        self.notify_signals([Signal({"error": error})], "status")
        # also report this on the management channel as warning
        self.notify_management_signal(StatusSignal(SignalStatus.warning,
                                                   error))
        # TODO: other values returned in other index other than errorIndex
        # TODO: have valid values ?

    def _handle_data(self, varBinds, starting_signal):
        """ Notify signals in the "default" output
        """
        # TODO: Is the status change handled
        # by BlockRouter implicitly or a call to notify_management_signal(ok)
        # needs to be done here ??
        for result in varBinds:
            if isinstance(result, tuple):
                self._enrich_signal(starting_signal, result)
            else:
                for inner_tuple in result:
                    self._enrich_signal(starting_signal, inner_tuple)
        self.notify_signals([starting_signal])

    def _enrich_signal(self, signal, result_tuple):
        setattr(
            signal,
            result_tuple[0].prettyPrint(),
            result_tuple[1].prettyPrint())

    def configure(self, context):
        """ Configure SNMP by creating data and transport for future
         GET requests
        """
        super().configure(context)
        self._data = self._create_data()
        self._transport = cmdgen.UdpTransportTarget(
            (self.agent_host, self.agent_port),
            timeout=self.timeout.seconds,
            retries=self.retries)

    def start(self):
        super().start()
        self._job = Job(self._request_GET, self.pool_interval, True)
        self._logger.info("SNMP polling started")

    def stop(self):
        if self._job:
            self._job.cancel()
            self._job = None
        self._logger.info("SNMP polling stopped")
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

    def configure(self, context):
        super().configure(context)
        self._logger.warning("THIS BLOCK IS DEPRECATED")
        self._logger.warning("Consider using the SNMPGet or SNMPWalk blocks")

    def _create_data(self):
        """ SNMP v1 and v2 use CommunityData
        """
        return cmdgen.CommunityData(self.community,
                                    mpModel=self.snmp_version.value)
