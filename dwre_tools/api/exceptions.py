

class SFCCException(Exception):
    pass

# Business Manager exceptions


class AccessDeniedException(SFCCException):
    pass


class PasswordExpiryException(AccessDeniedException):
    pass


class InactiveAccountException(AccessDeniedException):
    pass


# OCAPI


class OCAPIException(Exception):
    pass


class ClientAccessForbiddenException(OCAPIException):
    pass


class UserAccessForbiddenException(OCAPIException):
    pass


class FileNotExistsException(OCAPIException):
    pass
