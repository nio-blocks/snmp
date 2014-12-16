import datetime
from time import sleep
from unittest.mock import MagicMock
from nio.util.support.block_test_case import NIOBlockTestCase
from pysnmp.entity.rfc3413.oneliner.target import UdpTransportTarget
from snmp_block import SNMPBlock


class TestSNMPBlock(NIOBlockTestCase):

    def test_init(self):
        block = SNMPBlock()
        self.assertIsNone(block._data)
        self.assertIsNone(block._transport)
        self.assertIsNone(block._job)
        self.assertIsNotNone(block._cmdGen)
        self.assertEqual("127.0.0.1",block.agent_host)
        self.assertEqual(161,block.agent_port)
        self.assertEqual(datetime.timedelta(0, 1),block.timeout)
        self.assertEqual(5,block.retries)
        self.assertEqual(datetime.timedelta(0, 10),block.pool_interval)
        self.assertFalse(block.lookup_names)
        self.assertFalse(block.lookup_names)

    def test_configure(self):
        block = SNMPBlock()
        block._create_data = MagicMock()
        self.configure_block(block, {
            "agent_host": "127.0.0.1",
            "agent_port": 161,
            "community": "public",
            "oids": ["1.3.6.1.2.1.31.1.1.1.6.2"],
            "lookup_names": True
        })
        block._create_data.assert_called_once_with()
        self.assertEqual(UdpTransportTarget, block._transport.__class__)
        self.assertEqual(5, block._transport.retries)
        self.assertEqual(1, block._transport.timeout)

    def test_job_called(self):
        block = SNMPBlock()
        block._request_GET = MagicMock()
        self.configure_block(block, {
            "agent_host": "127.0.0.1",
            "agent_port": 161,
            "community": "public",
            "pool_interval": {"seconds": 1},
            "oids": ["1.3.6.1.2.1.31.1.1.1.6.2"],
            "lookup_names": True
        })
        block.start()
        sleep(2)
        block._request_GET.assert_called_with()
        block.stop()

    def test_request_get(self):
        block = SNMPBlock()
        block._data = MagicMock()
        block._transport = MagicMock()
        self.configure_block(block, {
            "agent_host": "127.0.0.1",
            "agent_port": 161,
            "community": "public",
            "pool_interval": {"seconds": 1},
            "oids": ["1.3.6.1.2.1.31.1.1.1.10.2",
                     "1.3.6.1.2.1.31.1.1.1.6.2",
                     "1.3.6.1.2.1.1.3.0",
                     "1.3.6.1.4.1.12356.101.14.5.1.15",
                     "1.3.6.1.4.1.12356.101.10.114.3.1.4"],
            "lookup_names": True
        })
        block._cmdGen.getCmd = MagicMock(return_value=(False, False, 0, {}))
        block._request_GET()
        block._cmdGen.getCmd.assert_called_once_with(
            block._data,
            block._transport,
            "1.3.6.1.2.1.31.1.1.1.10.2",
            "1.3.6.1.2.1.31.1.1.1.6.2",
            "1.3.6.1.2.1.1.3.0",
            "1.3.6.1.4.1.12356.101.14.5.1.15",
            "1.3.6.1.4.1.12356.101.10.114.3.1.4",
            lookupNames=True, lookupValues=False)


