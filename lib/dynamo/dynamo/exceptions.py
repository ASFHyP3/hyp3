"""Custom exceptions for the dynamo library."""


class DatabaseConditionException(Exception):
    """Raised when a DynamoDB condition expression check fails."""


class InsufficientCreditsError(Exception):
    """Raised when trying to submit jobs whose total cost exceeds the user's remaining credits."""


class InvalidApplicationStatusError(Exception):
    """Raised for an invalid user application status."""

    def __init__(self, user_id: str, application_status: str):
        super().__init__(f'User {user_id} has an invalid application status: {application_status}')



class UnexpectedApplicationStatusError(Exception):
    """Raised for an unexpected user application status."""
    help_url = 'https://hyp3-docs.asf.alaska.edu/using/request_access'


class NotStartedApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str):
        super().__init__(
            f'{user_id} must request access before submitting jobs. Visit {self.help_url}'
        )


class PendingApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str):
        super().__init__(
            f"{user_id}'s request for access is pending review. For more information, visit {self.help_url}"
        )


class ApprovedApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str):
        super().__init__(
            f"{user_id}'s request for access is already approved. For more information, visit {self.help_url}"
        )


class RejectedApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str):
        super().__init__(
            f"{user_id}'s request for access has been rejected. For more information, visit {self.help_url}"
        )
