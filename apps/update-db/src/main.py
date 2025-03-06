from typing import Any

from dynamo import jobs


def lambda_handler(event: dict, context: Any) -> None:
    jobs.update_job(event)
