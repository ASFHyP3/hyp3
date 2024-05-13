"""Custom exceptions for the dynamo library."""

REQUESTING_ACCESS_URL = 'https://hyp3-docs.asf.alaska.edu/using/requesting_access'


class DatabaseConditionException(Exception):
    """Raised when a DynamoDB condition expression check fails."""


class InvalidApplicationStatusError(Exception):
    """Raised for an invalid user application status."""

    def __init__(self, user_id: str, application_status: str):
        super().__init__(f'User {user_id} has an invalid application status: {application_status}')


class ResubmitPendingApplicationError(Exception):
    """Raised when a user with a pending application attempts to submit another application."""


class ResubmitRejectedApplicationError(Exception):
    """Raised when a user with a rejected application attempts to submit another application."""


class ResubmitApprovedApplicationError(Exception):
    """Raised when a user with an approved application attempts to submit another application."""


class InsufficientCreditsError(Exception):
    """Raised when trying to submit jobs whose total cost exceeds the user's remaining credits."""


class UnapprovedUserError(Exception):
    """Raised when an unapproved user attempts to submit jobs."""


class NotStartedApplicationError(UnapprovedUserError):
    def __init__(self, user_id: str):
        super().__init__(
            f'{user_id} must request access before submitting jobs. Visit {REQUESTING_ACCESS_URL}'
        )


class PendingApplicationError(UnapprovedUserError):
    def __init__(self, user_id: str):
        super().__init__(
            f"{user_id}'s request for access is pending review. For more information, visit {REQUESTING_ACCESS_URL}"
        )


class RejectedApplicationError(UnapprovedUserError):
    def __init__(self, user_id: str):
        super().__init__(
            f"{user_id}'s request for access has been rejected. For more information, visit {REQUESTING_ACCESS_URL}"
        )
