from unittest.mock import MagicMock
from nio.signal.base import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from ..snmp_get_block import SNMPGet


class TestSNMPGet(NIOBlockTestCase):

    def test_hard_coded_oid(self):
        """ Make sure that hard coded OIDs are queried properly """
        block = SNMPGet()
        myOID = "1.3.6.1.2.1.31.1.1.1.6.2"
        starting_signal = Signal({"existing_key": "existing_val"})
        self.configure_block(block, {
            "oids": [{"oid": myOID}]
        })
        block._cmdGen = MagicMock()
        block.start()
        # Send the starting signal, make sure everything was called correctly
        block.process_signals([starting_signal])
        args, kwargs = block._cmdGen.getCmd.call_args
        self.assertEqual(args[2], myOID)
        block.stop()
