from unittest.mock import MagicMock
from nio.common.signal.base import Signal
from nio.util.support.block_test_case import NIOBlockTestCase
from ..snmp_base_block import SNMPBase


SAMPLE_SNMP_RESPONSE = ("", False, 0, [])
SAMPLE_ERROR_SNMP_RESPONSE = ("ERROR", False, 0, [])
SAMPLE_ERROR_STATUS_SNMP_RESPONSE = ("", True, 123, [])


class TestSNMPBlock(NIOBlockTestCase):

    def test_hard_coded_oid(self):
        """ Make sure that hard coded OIDs are queried properly """
        block = SNMPBase()
        block._create_data = MagicMock()
        block._execute_snmp_request = MagicMock(
            return_value=SAMPLE_SNMP_RESPONSE)
        block._handle_data = MagicMock()

        myOID = "1.3.6.1.2.1.31.1.1.1.6.2"
        starting_signal = Signal({"existing_key": "existing_val"})

        self.configure_block(block, {
            "oids": [{"oid": myOID}]
        })
        block.start()

        # Send the starting signal, make sure everything was called correctly
        block.process_signals([starting_signal])
        args, kwargs = block._execute_snmp_request.call_args
        self.assertEqual(args[1], [myOID])
        block._handle_data.assert_called_once_with([], starting_signal)
        block.stop()

    def test_dynamic_oid(self):
        """ Make sure that dynamic OIDs are queried properly """
        block = SNMPBase()
        block._create_data = MagicMock()
        block._execute_snmp_request = MagicMock(
            return_value=SAMPLE_SNMP_RESPONSE)
        block._handle_data = MagicMock()

        myOID = "1.3.6.1.2.1.31.1.1.1.6.2"
        starting_signal = Signal({
            "existing_key": "existing_val",
            "oid": myOID
        })

        self.configure_block(block, {
            "oids": [{"oid": "{{ $oid }}"}]
        })
        block.start()

        # Send the starting signal, make sure everything was called correctly
        block.process_signals([starting_signal])
        args, kwargs = block._execute_snmp_request.call_args
        self.assertEqual(args[1], [myOID])
        block._handle_data.assert_called_once_with([], starting_signal)
        block.stop()

    def test_bad_oid(self):
        """ Make sure that errors determining the OID aren't queried """
        block = SNMPBase()
        block._create_data = MagicMock()
        block._execute_snmp_request = MagicMock(
            return_value=SAMPLE_SNMP_RESPONSE)
        block._handle_data = MagicMock()

        myOID = "1.3.6.1.2.1.31.1.1.1.6.2"
        starting_signal = Signal({
            "existing_key": "existing_val",
            "not an oid": myOID
        })

        self.configure_block(block, {
            "oids": [{"oid": "{{ $oid }}"}]
        })
        block.start()

        # Send the bad signal, make sure execute was never called
        block.process_signals([starting_signal])
        self.assertFalse(block._execute_snmp_request.called)
        block.stop()

    def test_error_statuses(self):
        """ Make sure that exceptions in queries are handled """
        block = SNMPBase()
        block._create_data = MagicMock()

        # We will call execute 4 times. It will throw 3 errors and 1 valid
        block._execute_snmp_request = MagicMock(
            side_effect=[SAMPLE_ERROR_SNMP_RESPONSE,
                         SAMPLE_ERROR_STATUS_SNMP_RESPONSE,
                         SAMPLE_SNMP_RESPONSE,
                         Exception])
        block._handle_data = MagicMock()

        myOID = "1.3.6.1.2.1.31.1.1.1.6.2"
        self.configure_block(block, {
            "oids": [{"oid": myOID}]
        })
        block.start()

        # Send 4 signals to the block, causing 4 requests to go out
        block.process_signals([Signal({"sig": i}) for i in range(4)])

        # Execute request should have been called 4 times
        self.assertEqual(block._execute_snmp_request.call_count, 4)

        # Handle data should only be called for the valid response
        self.assertEqual(block._handle_data.call_count, 1)
        self.assertEqual(block._handle_data.call_args[0][0], [])
        block.stop()

    def test_host_port_expression_props(self):
        """ Test that host and port expressions props work """
        block = SNMPBase()
        block._create_data = MagicMock()
        block._execute_snmp_request = MagicMock(
            return_value=SAMPLE_SNMP_RESPONSE)
        block._handle_data = MagicMock()
        myOID = "1.3.6.1.2.1.31.1.1.1.6.2"
        ip = "0.0.0.0"
        port = 1611
        starting_signal = Signal({
            "ip": ip,
            "port": port
        })
        self.configure_block(block, {
            "oids": [{"oid": myOID}],
            "agent_host": "{{ $ip }}",
            "agent_port": "{{ $port }}"
        })
        block.start()
        # Send the starting signal, make sure everything was called correctly
        block.process_signals([starting_signal])
        args, kwargs = block._execute_snmp_request.call_args
        self.assertEqual(args[1], [myOID])
        block._handle_data.assert_called_once_with([], starting_signal)
        block.stop()

    def test_invalid_host_expression_prop(self):
        """ Test that host expression props fail gracefully """
        block = SNMPBase()
        block._create_data = MagicMock()
        block.execute_request = MagicMock()
        myOID = "1.3.6.1.2.1.31.1.1.1.6.2"
        ip = "0.0.0.0"
        port = 1611
        starting_signal = Signal({
            "ip": ip,
            "port": port
        })
        self.configure_block(block, {
            "oids": [{"oid": myOID}],
            "agent_host": "{{ ip }}",
        })
        block.start()
        # Send the starting signal, make sure everything was called correctly
        block.process_signals([starting_signal])
        self.assertEqual(0, block.execute_request.call_count)
        block.stop()

    def test_invalid_port_expression_prop(self):
        """ Test that port expression props fail gracefully """
        block = SNMPBase()
        block._create_data = MagicMock()
        block.execute_request = MagicMock()
        myOID = "1.3.6.1.2.1.31.1.1.1.6.2"
        ip = "0.0.0.0"
        port = 1611
        starting_signal = Signal({
            "ip": ip,
            "port": port
        })
        self.configure_block(block, {
            "oids": [{"oid": myOID}],
            "agent_port": "{{ port }}"
        })
        block.start()
        # Send the starting signal, make sure everything was called correctly
        block.process_signals([starting_signal])
        self.assertEqual(0, block.execute_request.call_count)
        block.stop()
