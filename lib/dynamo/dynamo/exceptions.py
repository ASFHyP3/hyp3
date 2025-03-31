"""Custom exceptions for the dynamo library."""


class DatabaseConditionException(Exception):
    """Raised when a DynamoDB condition expression check fails and does not warrant a more specific exception type."""


class AccessCodeError(Exception):
    """Raised when a user application includes an invalid or expired access code."""


class InsufficientCreditsError(Exception):
    """Raised when trying to submit jobs whose total cost exceeds the user's remaining credits."""


class UpdateJobNotFoundError(Exception):
    """Raised when a user attempts to update a job that doesn't exist."""


class UpdateJobForDifferentUserError(Exception):
    """Raised when a user attempts to update a different user's job."""


class InvalidApplicationStatusError(Exception):
    """Raised for an invalid user application status."""

    def __init__(self, user_id: str, application_status: str) -> None:
        super().__init__(f'User {user_id} has an invalid application status: {application_status}')


class UnexpectedApplicationStatusError(Exception):
    """Raised for an unexpected user application status."""

    help_url = 'https://hyp3-docs.asf.alaska.edu/using/requesting_access'


class NotStartedApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str) -> None:
        super().__init__(f'{user_id} must request access before submitting jobs. Visit {self.help_url}')


class PendingApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str) -> None:
        super().__init__(
            f"{user_id}'s request for access is pending review. For more information, visit {self.help_url}"
        )


class ApprovedApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str) -> None:
        super().__init__(
            f"{user_id}'s request for access is already approved. For more information, visit {self.help_url}"
        )


class RejectedApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str) -> None:
        super().__init__(
            f"{user_id}'s request for access has been rejected. For more information, visit {self.help_url}"
        )
