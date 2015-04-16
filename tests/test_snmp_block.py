import datetime
from unittest.mock import MagicMock
from nio.common.signal.base import Signal
from nio.common.signal.status import StatusSignal, SignalStatus
from nio.util.support.block_test_case import NIOBlockTestCase
from pysnmp.entity.rfc3413.oneliner.target import UdpTransportTarget
from ..snmp_block import SNMPBlock, BaseSNMPBlock
from pysnmp.proto.api.v2c import OctetString
from pysnmp.proto.rfc1902 import ObjectName


class TestSNMPBlock(NIOBlockTestCase):

    def test_init(self):
        block = SNMPBlock()
        self.assertIsNone(block._data)
        self.assertIsNone(block._transport)
        self.assertIsNone(block._job)
        self.assertIsNotNone(block._cmdGen)
        self.assertEqual("127.0.0.1", block.agent_host)
        self.assertEqual(161, block.agent_port)
        self.assertEqual(datetime.timedelta(0, 1), block.timeout)
        self.assertEqual(5, block.retries)
        self.assertFalse(block.lookup_names)
        self.assertFalse(block.lookup_names)

    def configure_block_with_oids(self, block, oids, exclude_existing=True):
        self.configure_block(block, {
            "agent_host": "127.0.0.1",
            "agent_port": 161,
            "exclude_existing": exclude_existing,
            "community": "public",
            "oids": [{'oid': oid} for oid in oids],
            "lookup_names": True
        })

    def test_configure(self):
        block = SNMPBlock()
        block._create_data = MagicMock()
        self.configure_block_with_oids(block, ["1.3.6.1.2.1.31.1.1.1.6.2"])
        block._create_data.assert_called_once_with()
        self.assertEqual(UdpTransportTarget, block._transport.__class__)
        self.assertEqual(5, block._transport.retries)
        self.assertEqual(1, block._transport.timeout)

    def test_request_made_with_signal(self):
        block = SNMPBlock()
        block.execute_request = MagicMock()
        my_signal = Signal({"test_key": "test_val"})
        my_oid = ["1.3.6.1.2.1.31.1.1.1.6.2"]
        self.configure_block_with_oids(block, my_oid, False)
        block.start()
        block.process_signals([my_signal])
        block.execute_request.assert_called_with(my_oid, my_signal)
        block.stop()

    def test_request_made(self):
        block = SNMPBlock()
        block.execute_request = MagicMock()
        my_oid = ["1.3.6.1.2.1.31.1.1.1.6.2"]
        self.configure_block_with_oids(block, my_oid)
        block.start()
        block.process_signals([Signal()])
        block.execute_request.assert_called_with(my_oid, None)
        block.stop()

    def test_request_get(self):
        block = SNMPBlock()
        block._data = MagicMock()
        block._transport = MagicMock()
        my_oids = ["1.3.6.1.2.1.31.1.1.1.10.2",
                   "1.3.6.1.2.1.31.1.1.1.6.2",
                   "1.3.6.1.2.1.1.3.0",
                   "1.3.6.1.4.1.12356.101.14.5.1.15",
                   "1.3.6.1.4.1.12356.101.10.114.3.1.4"]
        self.configure_block_with_oids(block, my_oids)
        block._cmdGen.getCmd = MagicMock(return_value=("", False, 0, []))
        block.process_signals([Signal()])
        block._cmdGen.getCmd.assert_called_once_with(
            block._data,
            block._transport,
            *my_oids,
            lookupNames=True, lookupValues=False)

    def test_error_handling(self):
        block = SNMPBlock()
        block._data = MagicMock()
        block._transport = MagicMock()
        block._handle_error = MagicMock()
        self.configure_block_with_oids(block, ["1.3.6.1.2.1.31.1.1.1.6.2"])
        block._cmdGen.getCmd = MagicMock(
            return_value=("No response before timeout", False, 0, {}))
        block.process_signals([Signal()])
        block._handle_error.assert_called_once_with(
            "No response before timeout")

    def test_error_handling_signal(self):

        def my_notify_mgmt_signal(signal):
            self.assertEqual(StatusSignal, signal.__class__)
            self.assertEqual(SignalStatus.error, signal.status)
            self.assertEqual("No response before timeout", signal.msg)

        block = SNMPBlock()
        block._data = MagicMock()
        block._transport = MagicMock()
        block.notify_management_signal = my_notify_mgmt_signal
        self.configure_block_with_oids(block, ["1.3.6.1.2.1.31.1.1.1.6.2"])
        block._cmdGen.getCmd = MagicMock(
            return_value=("No response before timeout", False, 0, {}))
        block.process_signals([Signal()])

    def test_error_status_handling(self):

        def my_handle_signal(signals, output):
            self.assertEqual(1, len(signals))
            self.assertEqual("status", output)
            self.assertEqual("b'low battery' at 1.3.6.1.2.1.31.1.1.1.6.2",
                             signals[0].error)

        def my_notify_mgmt_signal(signal):
            self.assertEqual(StatusSignal, signal.__class__)
            self.assertEqual(SignalStatus.warning, signal.status)
            self.assertEqual("b'low battery' at 1.3.6.1.2.1.31.1.1.1.6.2",
                             signal.msg)

        block = SNMPBlock()
        block._data = MagicMock()
        block._transport = MagicMock()
        block.notify_management_signal = my_notify_mgmt_signal
        block.notify_signals = my_handle_signal
        self.configure_block_with_oids(block, ["1.3.6.1.2.1.31.1.1.1.6.2"])
        block._cmdGen.getCmd = MagicMock(
            return_value=(None,
                          OctetString("low battery"),
                          1,
                          [(ObjectName("1.3.6.1.2.1.31.1.1.1.6.2"),
                            OctetString(""))]))
        block.process_signals([Signal()])

    def test_create_data(self):
        block = BaseSNMPBlock()
        with self.assertRaises(NotImplementedError):
            block._create_data()
