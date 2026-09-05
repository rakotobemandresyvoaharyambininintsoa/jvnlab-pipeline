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


def _compute_wait(status, res, retries):
    if status == 429:
        return res.get("retry_after", 1)
    return (2 ** retries) + random.random()


def _fetch_page_with_retry(siren, page, max_retries):
    """Recupere une page avec retry. Retourne (data, next_page) ou (None, None) si echec definitif."""
    retries = 0

    while retries < max_retries:

        throttle()
        res = mock_api(siren, page)
        status = res["status"]

        if status == 200:
            return res.get("data", []), res.get("next")

        if status in FATAL_ERRORS:
            return None, None

        if status in TRANSIENT_ERRORS:
            time.sleep(_compute_wait(status, res, retries))
            retries += 1

    return None, None


def fetch_with_retry(siren, max_retries=5):

    page = 1
    results = []

    while page:
        data, next_page = _fetch_page_with_retry(siren, page, max_retries)

        if data is None:
            return None

        results.extend(data)
        page = next_page

    return results
