# ----------------------------------------------------------
# Helper
# ----------------------------------------------------------


def convert_security_uid(id):
    if isinstance(id, NoSecurityUid):
        return super(NoSecurityUid, id).__int__()
    return id


# ----------------------------------------------------------
# Model
# ----------------------------------------------------------


class NoSecurityUid(int):
    def __int__(self):
        return self

    def __eq__(self, other):
        if isinstance(other, int):
            return False
        return super(NoSecurityUid, self).__int__() == other

    def __hash__(self):
        return super(NoSecurityUid, self).__hash__()
