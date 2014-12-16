from nio.util.support.block_test_case import NIOBlockTestCase
from unittest2 import skip
from snmp_block import SNMPBlock
from pysnmp import debug

@skip
class TestSNMPGet(NIOBlockTestCase):

    def my_notify_signals(self, signals, output_id='default'):
        for signal in signals:
            print(str(signal))

    def test_configure(self):
        blk = SNMPBlock()
        blk.notify_signals = self.my_notify_signals
        # debug.setLogger(debug.Debug('all'))
        self.configure_block(blk, {
            "type": "SNMPManager",
            "name": "SNMPClientManager",
            "agent_host": "65.112.205.130",
            "agent_port": 161,
            "community": "NIOLAB",
            "oids": "1.3.6.1.2.1.31.1.1.1.6.2",
            "lookup_names": True
        })
        blk._request_GET()

    def test_configure2(self):
        blk = SNMPBlock()
        blk.notify_signals = self.my_notify_signals
        # debug.setLogger(debug.Debug('all'))
        self.configure_block(blk, {
            "type": "SNMPManager",
            "name": "SNMPClientManager",
            "agent_host": "65.112.205.130",
            "agent_port": 161,
            "community": "NIOLAB",
            "oids": "1.3.6.1.2.1.31.1.1.1.10.2, 1.3.6.1.2.1.31.1.1.1.6.2,1.3.6.1.2.1.1.3.0",
                    # "1.3.6.1.4.1.12356.101.14.5.1.15, 1.3.6.1.4.1.12356.101.10.114.3.1.4"
            "lookup_names": True
        })
        blk._request_GET()

    def test_configure_demo(self):
        blk = SNMPBlock()
        # debug.setLogger(debug.Debug('all'))
        blk.notify_signals = self.my_notify_signals
        self.configure_block(blk, {
            "type": "SNMPManager",
            "name": "SNMPClientManager",
            "agent_host": "demo.snmplabs.com",
            "agent_port": 161,
            "community": "public",
            "oids": "1.3.6.1.2.1.1.1.0",
            "lookup_names": True
        })
        blk._request_GET()

    def test_configure_demo2(self):
        from pysnmp.entity.rfc3413.oneliner import cmdgen

        cmdGen = cmdgen.CommandGenerator()
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
            cmdgen.CommunityData('public'),
            cmdgen.UdpTransportTarget(('demo.snmplabs.com', 161)),
            # "1.3.6.1.2.1.1.5.0")
            cmdgen.MibVariable('SNMPv2-MIB', 'sysName', 0))
        # )

        # Check for errors and print out results
        if errorIndication:
            print(errorIndication)
        else:
            if errorStatus:
                print('%s at %s' % (
                    errorStatus.prettyPrint(),
                    errorIndex and varBinds[int(errorIndex)-1] or '?'
                    )
                )
            else:
                for name, val in varBinds:
                    print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))