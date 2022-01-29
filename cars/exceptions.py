class ProjectError(Exception):
    pass


class InvalidVendor(ProjectError):
    pass


class InvalidModel(ProjectError):
    pass


class InvalidGeneration(ProjectError):
    pass


class LogicError(ProjectError):
    pass


class NetworkError(ProjectError):
    pass


class ApiRequestError(NetworkError):
    pass


class InvalidConstantValue(ProjectError):
    pass
