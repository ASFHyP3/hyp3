import random


def lambda_handler(event: dict, _) -> bool:
    # TODO: search archive
    #  - if exists: update job record, refund user's credits, return True
    #  - if does not exist: return False
    print(event)
    return bool(random.randint(0, 1))
