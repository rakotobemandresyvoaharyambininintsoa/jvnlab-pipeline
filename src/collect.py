import time
import random


class RateLimitError(Exception):
    """Levee quand l'API simulee renvoie une erreur 429 (rate limit)."""


class ServerError(Exception):
    """Levee quand l'API simulee renvoie une erreur 5xx."""


def fetch_siren_data(siren):
    """
    Mock API SIRENE avec :
    - pagination simulee
    - retry
    - erreurs 429 / 5xx
    """

    pages = 3
    results = []

    for page in range(1, pages + 1):

        retries = 0

        while retries < 3:
            try:

                if random.random() < 0.15:
                    raise RateLimitError("429 rate limit")

                if random.random() < 0.10:
                    raise ServerError("500 server error")

                results.append({
                    "siren": siren,
                    "page": page,
                    "status": "active",
                    "name": f"Company {siren}"
                })

                break

            except (RateLimitError, ServerError):
                retries += 1
                wait = (2 ** retries) + random.random()
                time.sleep(wait)

    return results
