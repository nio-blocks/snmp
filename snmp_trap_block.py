"""

  SNMP Trap Block

"""
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp, udp6
from pyasn1.codec.ber import decoder
from pysnmp.proto import api

from nio.common.block.attribute import Output
from nio.common.block.base import Block
from nio.common.signal.base import Signal
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.string import StringProperty
from nio.common.discovery import Discoverable, DiscoverableType
from nio.modules.threading import Thread

from . import oid_parser


@Output("trap")
@Discoverable(DiscoverableType.block)
class SNMPTrapBlock(Block):

    ip_address = StringProperty(title='IP Address', default='127.0.0.1')
    port = IntProperty(title='Port', default=162)

    def __init__(self):
        super().__init__()
        self._transport_dispatcher = None
        self._dispatcher_thread = None

    def configure(self, context):
        super().configure(context)
        self._transport_dispatcher = AsynsockDispatcher()
        # register trap-receiver callback
        self._transport_dispatcher.registerRecvCbFun(self._on_trap)
        self._register_transports()

    def _register_transports(self):
        # UDP/IPv4
        self._transport_dispatcher.registerTransport(
            udp.domainName, udp.UdpSocketTransport().openServerMode(
                (self.ip_address, self.port)))
        # UDP/IPv6
        self._transport_dispatcher.registerTransport(
            udp6.domainName, udp6.Udp6SocketTransport().openServerMode(
                ('::1', self.port)))

    def start(self):
        super().start()
        self._dispatcher_thread = \
            TrapDispatcherThread(self._transport_dispatcher, self._logger)
        self._dispatcher_thread.start()

    def stop(self):
        if self._dispatcher_thread:
            self._dispatcher_thread.stop()
            self._dispatcher_thread.join()
            self._dispatcher_thread = None

        super().stop()

    def _on_trap(self, transport_dispatcher, transport_domain,
                 transport_address, whole_msg):
        """ This method is called from pysnmp whenever a trap is received
        """
        self._logger.debug('Trap received')
        signals = []
        while whole_msg:
            signal_data = {}
            msg_ver = int(api.decodeMessageVersion(whole_msg))
            if msg_ver in api.protoModules:
                p_mod = api.protoModules[msg_ver]
            else:
                self._logger.warning('Unsupported SNMP version %s' % msg_ver)
                return
            req_msg, whole_msg = decoder.decode(
                whole_msg, asn1Spec=p_mod.Message(),)

            self._logger.info('Notification message from %s:%s: ' % (
                transport_domain, transport_address))
            signal_data["transport_domain"] = \
                str(oid_parser(transport_domain))
            signal_data["transport_address"] = \
                str(oid_parser(transport_address))

            req_pdu = p_mod.apiMessage.getPDU(req_msg)
            if req_pdu.isSameTypeWith(p_mod.TrapPDU()):
                if msg_ver == api.protoVersion1:
                    signal_data["enterprise"] = \
                        p_mod.apiTrapPDU.getEnterprise(req_pdu).prettyPrint()
                    signal_data["agent address"] = \
                        p_mod.apiTrapPDU.getAgentAddr(req_pdu).prettyPrint()
                    signal_data["generic trap"] = \
                        p_mod.apiTrapPDU.getGenericTrap(req_pdu).prettyPrint()
                    signal_data["specific trap"] = \
                        p_mod.apiTrapPDU.getSpecificTrap(req_pdu).prettyPrint()
                    signal_data["uptime"] = \
                        p_mod.apiTrapPDU.getTimeStamp(req_pdu).prettyPrint()
                    var_binds = p_mod.apiTrapPDU.getVarBindList(req_pdu)
                else:
                    var_binds = p_mod.apiPDU.getVarBindList(req_pdu)
                signal_data["var-binds"] = {}
                for oid, val in var_binds:
                    signal_data["var-binds"][str(oid_parser(oid._value))] = \
                        self._get_var_bind_data(val)
            signals.append(Signal(signal_data))
        if len(signals):
            self.notify_signals(signals, "trap")

    def _get_var_bind_data(self, val):
        """ Processes data associated to a given var bind oid

        Args:
            val: value associated to an oid

        Returns:
            data in dictionary form
        """
        data = {}
        if hasattr(val, "_componentValues"):
            for idx in range(len(val._componentValues)):
                if val._componentValues[idx] is not None:
                    component_type = val.getComponentType()
                    if component_type is not None:
                        data[component_type.getNameByPosition(idx)] = \
                            self._get_var_bind_data(val._componentValues[idx])
        elif hasattr(val, "_value"):
            if oid_parser.validate(val._value):
                return str(oid_parser(val._value))
            return val._value
        else:
            if oid_parser.validate(val):
                return str(oid_parser(val))
            return str(val)
        return data


class TrapDispatcherThread(Thread):

    def __init__(self, transport_dispatcher, logger):
        super().__init__()
        self._transport_dispatcher = transport_dispatcher
        self._logger = logger
        self.daemon = True

    def run(self):
        self._serve_forever()

    def stop(self):
        self._transport_dispatcher.closeDispatcher()
        self._transport_dispatcher.jobFinished(1)

    def _serve_forever(self):
        self._transport_dispatcher.jobStarted(1)
        try:
            self._transport_dispatcher.runDispatcher()
        except KeyboardInterrupt:
            self._transport_dispatcher.closeDispatcher()
        except Exception:
            self._logger.exception("Dispatcher exception")
