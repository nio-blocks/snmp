from pysnmp.entity.rfc3413.oneliner import cmdgen
from nio.common.block.base import Block
from nio.common.signal.base import Signal
from nio.metadata.properties import TimeDeltaProperty, BoolProperty, \
    ListProperty, IntProperty, StringProperty, \
    ExpressionProperty, PropertyHolder
from .mixins.limit_lock.limit_lock import LimitLock


class OIDProperty(PropertyHolder):
    oid = ExpressionProperty(
        title='OID',
        default='{{ $oid }}',
        attr_default=AttributeError)


class SNMPStatusException(Exception):

    def __init__(self, status, index):
        super().__init__("SNMP Status: {}, Index: {}".format(status, index))


class SNMPException(Exception):
    pass


class SNMPBase(LimitLock, Block):

    """ A base block implementing a SNMP Manager

    Request SNMP GET ops to SNMP Agents for retrieving monitor data and
    publish them as signals
    """

    agent_host = ExpressionProperty(title="SNMP Agent Url", default='127.0.0.1')
    agent_port = ExpressionProperty(title="SNMP Agent Port", default='161')
    timeout = TimeDeltaProperty(title='Request Timeout',
                                default={"seconds": 1})
    retries = IntProperty(title="SNMP Retries", default=5)
    exclude_existing = BoolProperty(
        title="Exclude Existing Values", default=False)
    lookup_names = BoolProperty(title="Look up OID names", default=False)
    lookup_values = BoolProperty(title="Look up OID values", default=False)
    oids = ListProperty(OIDProperty, title="List of OID")

    def __init__(self):
        super().__init__()
        self._cmdGen = cmdgen.CommandGenerator()
        self._data = None
        self._job = None

    def configure(self, context):
        """ Configure SNMP by creating data and transport for future
         GET requests
        """
        super().configure(context)
        self._data = self._create_data()

    def process_signals(self, signals, input_id='default'):
        for signal in signals:
            try:
                self._execute_with_lock(
                    self._process_signal, 20, signal=signal)
            except:
                # Exceptions are already logged inside _process_signal
                # Nothing special needs to happen here
                pass

    def _process_signal(self, signal):
        valid_oids = []
        for oid in self.oids:
            try:
                next_oid = oid.oid(signal)
                valid_oids.append(next_oid)
            except:
                self._logger.exception(
                    "Could not determine OID from {}".format(oid))
        transport = None
        try:
            host = self.agent_host(signal)
            port = int(self.agent_port(signal))
            transport = cmdgen.UdpTransportTarget(
                (host, port),
                timeout=self.timeout.total_seconds(),
                retries=self.retries)
        except:
            self._logger.exception(
                "Could not determine transport for signal: {}".format(signal))
            return
        starting_signal = None if self.exclude_existing else signal
        if transport and valid_oids:
            self.execute_request(transport, valid_oids, starting_signal)

    def execute_request(self, transport, oids, starting_signal=None):
        """ Executes SNMP GET request
        """
        try:
            self._logger.debug("Make snmp request: {}".format(transport))
            result = self._make_snmp_request(transport, oids)
            self._logger.debug("Handle snmp response: {}".format(result))
            if starting_signal:
                self._handle_data(result, starting_signal)
            else:
                self._handle_data(result, Signal())
        except SNMPStatusException:
            # TODO: Make this output on status ouptut
            self._logger.exception("Error status returned for transport:"
                                   " {}".format(transport))
        except SNMPException:
            self._logger.exception("Error returned"
                                   " {}".format(transport))
        except:
            self._logger.exception("Unexpected exception in SNMP"
                                   " {}".format(transport))

    def _create_data(self):
        """ Method to be override in inherited classes
          Returns the data required by cmdGen for executing SNMP GET
          operations on an Agent
        """
        raise NotImplementedError()

    def _make_snmp_request(self, transport, oids):
        """ Execute the request and handle errors or responses """
        error_indication, error_status, error_index, var_binds = \
            self._execute_snmp_request(transport, oids)
        # Check for errors
        if error_indication:
            raise SNMPException(error_indication)
        elif error_status:
            raise SNMPStatusException(error_status, error_index)
        return var_binds

    def _execute_snmp_request(self, oids):
        """ Override this in the child block to make the proper request """
        raise NotImplementedError()

    def _handle_data(self, var_binds, starting_signal):
        """ Override this in the child block to make the proper request """
        raise NotImplementedError()

    def _enrich_signal(self, signal, result_tuple):
        """ Enrich a signal with an SNMP result tuple """
        setattr(
            signal,
            result_tuple[0].prettyPrint(),
            result_tuple[1].prettyPrint())
