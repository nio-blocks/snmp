class oid_parser(object):
    def __init__(self, oid):
        self._oid = oid

    def __str__(self):
        return ".".join(map(str, self._oid))

    @classmethod
    def validate(cls, oid_in):
        if not isinstance(oid_in, tuple):
            return False
        for elem in oid_in:
            if not isinstance(elem, int):
                return False
        return True
