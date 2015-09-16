from unittest.mock import MagicMock
from nio.common.signal.base import Signal
from nio.util.support.block_test_case import NIOBlockTestCase
from ..snmp_walk_block import SNMPWalk


SAMPLE_SNMP_RESPONSE = ("", False, 0, [])
SAMPLE_ERROR_SNMP_RESPONSE = ("ERROR", False, 0, [])
SAMPLE_ERROR_STATUS_SNMP_RESPONSE = ("", True, 123, [])


class TestSNMPWalk(NIOBlockTestCase):

    def test_hard_coded_oid(self):
        """ Make sure that hard coded OIDs are queried properly """
        block = SNMPWalk()
        myOID = "1.3.6.1.2.1.31.1.1.1.6.2"
        starting_signal = Signal({"existing_key": "existing_val"})
        self.configure_block(block, {
            "oids": [{"oid": myOID}]
        })
        block._cmdGen = MagicMock()
        block.start()
        # Send the starting signal, make sure everything was called correctly
        block.process_signals([starting_signal])
        args, kwargs = block._cmdGen.nextCmd.call_args
        self.assertEqual(args[2], myOID)
        block.stop()
