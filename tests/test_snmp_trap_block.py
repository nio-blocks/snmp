from unittest.mock import MagicMock, patch
from pysnmp.proto.error import ProtocolError
from nio.testing.block_test_case import NIOBlockTestCase
from ..snmp_trap_block import SNMPTrap, TrapDispatcherThread


class TestSNMPTrapBlock(NIOBlockTestCase):

    def test_init(self):
        block = SNMPTrap()
        self.assertIsNone(block._transport_dispatcher)
        self.assertIsNone(block._dispatcher_thread)
        self.assertEqual("127.0.0.1", block.ip_address())
        self.assertEqual(162, block.port())

    def test_configure(self):
        block = SNMPTrap()
        block._register_transports = MagicMock()

        self.configure_block(block, {
            "ip_address": "10.0.0.1",
            "port": 9999})
        self.assertIsNotNone(block._transport_dispatcher)
        self.assertIsNone(block._dispatcher_thread)
        self.assertEqual(block.ip_address(), "10.0.0.1")
        self.assertEqual(block.port(), 9999)
        self.assertEqual(block._register_transports.call_count, 1)

    @patch(SNMPTrap.__module__ + '.TrapDispatcherThread')
    def test_start_stop(self, thread_mock):

        class DispatcherMyThread(TrapDispatcherThread):
            def __init__(self, transport_dispatcher, logger):
                super().__init__(transport_dispatcher, logger)
                self.start = MagicMock()
                self.stop = MagicMock()
                self.join = MagicMock()

        block = SNMPTrap()
        my_thread = DispatcherMyThread(None, None)
        thread_mock.return_value = my_thread

        block.start()
        self.assertIsNotNone(block._dispatcher_thread)
        self.assertTrue(my_thread.start.called)
        self.assertFalse(my_thread.stop.called)
        self.assertFalse(my_thread.join.called)

        block.stop()
        self.assertIsNone(block._dispatcher_thread)
        self.assertTrue(my_thread.stop.called)
        self.assertTrue(my_thread.join.called)

    def test_on_trap(self):
        """ Provides coverage for _on_trap method
        """

        block = SNMPTrap()
        block._on_trap(None, (1, 3, 6, 1, 1), ('127.0.0.1', 49999), None)
        self.assert_num_signals_notified(0, block, "trap")

        with self.assertRaises(ProtocolError):
            block._on_trap(None, (1, 3, 6, 1, 1), ('127.0.0.1', 49999),
                           "trash")
        self.assert_num_signals_notified(0, block, "trap")

        # use valid data
        msg = b'0Y\x02\x01\x01\x04\x06public\xa7L\x02\x04\x00\xb7\x19\x89\
        x02\x01\x00\x02\x01\x000>0\r\x06\x08+\x06\x01\x02\x01\x01\x03\x00C\
        x01\x000\x17\x06\n+\x06\x01\x06\x03\x01\x01\x04\x01\x00\x06\t+\x06\
        x01\x06\x03\x01\x01\x05\x010\x14\x06\x08+\x06\x01\x02\x01\x01\x05\
        x00\x04\x08new name'
        # attempt to deliver signal since it throws a block router exception
        with self.assertRaises(AttributeError):
            block._on_trap(None, (1, 3, 6, 1, 1), ('127.0.0.1', 49999), msg)
        self.assert_num_signals_notified(0, block, "trap")

        # mock transport settings
        block._register_transports = MagicMock()
        self.configure_block(block, {})
        # assert that a signal was notified on 'trap' output
        block._on_trap(None, (1, 3, 6, 1, 1), ('127.0.0.1', 49999), msg)
        self.assert_num_signals_notified(1, block, "trap")

    def test_var_bind_data(self):
        """ Provides coverage for _get_var_bind_data method
        """
        block = SNMPTrap()

        from pysnmp.proto.rfc1905 import _BindValue
        from pysnmp.proto.rfc1902 import ObjectSyntax, TimeTicks

        # add it an object value
        val = _BindValue()
        composed_object1 = ObjectSyntax()
        val._componentValues.append(composed_object1)

        # add it a simple value
        simple_syntax = TimeTicks()
        simple_syntax._value = 9
        val._componentValues.append(simple_syntax)

        var_bind_data = block._get_var_bind_data(val)
        self.assertIn('unSpecified',  var_bind_data)
        self.assertEqual(var_bind_data['unSpecified'],  9)
        self.assertIn('value',  var_bind_data)
        self.assertEqual(var_bind_data['value'],  {})
