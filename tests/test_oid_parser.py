from nio.testing.block_test_case import NIOBlockTestCase
from .. import oid_parser


class Test_OID_Parser(NIOBlockTestCase):

    def test_valid_oid(self):
        pysnmp_oid = (1, 3, 1, 4, 5, 6)
        self.assertTrue(oid_parser.validate(pysnmp_oid))
        oid = str(oid_parser(pysnmp_oid))
        self.assertEqual(oid, "1.3.1.4.5.6")

    def test_invalid_oids(self):
        self.assertFalse(oid_parser.validate((1, 3, "invalid", 4, 5, 6)))
        self.assertFalse(oid_parser.validate("not a tuple"))

