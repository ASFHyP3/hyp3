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


class NotStartedApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str):
        # TODO replace <url> with URL to the application form for the given deployment
        super().__init__(
            f'User {user_id} has not yet applied for a monthly credit allotment.'
            ' Please visit <url> to submit your application.'
        )


class PendingApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str):
        super().__init__(f'User {user_id} has a pending application, please try again later.')


class ApprovedApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str):
        super().__init__(f'The application for user {user_id} has already been approved.')


class RejectedApplicationError(UnexpectedApplicationStatusError):
    def __init__(self, user_id: str):
        super().__init__(
            f'The application for user {user_id} has been rejected.'
            ' For more information, please email ASF User Services at: uso@asf.alaska.edu'
        )
