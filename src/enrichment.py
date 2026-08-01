import time
import random

TRANSIENT_ERRORS = {429, 500, 502, 503}
FATAL_ERRORS = {400, 401, 403, 404}

LAST_CALL = 0
RATE_LIMIT = 5


def throttle():
    global LAST_CALL
    wait = 1 / RATE_LIMIT
    elapsed = time.time() - LAST_CALL
    if elapsed < wait:
        time.sleep(wait - elapsed)
    LAST_CALL = time.time()


def mock_api(siren, page=1):

    if random.random() < 0.1:
        return {"status": 500}

    if random.random() < 0.1:
        return {"status": 429, "retry_after": 1}

    if page > 2:
        return {"status": 200, "data": [], "next": None}

    return {
        "status": 200,
        "data": [{"siren": siren, "name": f"Company {siren}"}],
        "next": page + 1
    }


def fetch_with_retry(siren, max_retries=5):

    page = 1
    results = []

    while page:

        retries = 0

        while retries < max_retries:

            throttle()
            res = mock_api(siren, page)
            status = res["status"]

            if status == 200:
                results.extend(res.get("data", []))
                page = res.get("next")
                break

            # fatal error
            if status in FATAL_ERRORS:
                return None

            # retryable
            if status in TRANSIENT_ERRORS:
                if status == 429:
                    time.sleep(res.get("retry_after", 1))

                else:
                    time.sleep((2 ** retries) + random.random())

                retries += 1
                continue

        else:
            return None

    return results