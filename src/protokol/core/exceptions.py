class ProtocolError(Exception):
    """Base exception for SDK."""
    pass


class StepExecutionError(ProtocolError):
    """Raised when a step fails execution."""
    pass


class StepNotFoundError(ProtocolError):
    """Raised when a step is missing in a flow."""
    pass


class FlowExecutionError(ProtocolError):
    """Raised when flow execution fails."""
    pass


class ValidationError(ProtocolError):
    """Raised when schema validation fails."""
    pass