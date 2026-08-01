import time
import random


def fetch_siren_data(siren):
    """
    Mock API SIRENE avec :
    - pagination simulée
    - retry
    - erreurs 429 / 5xx
    """

    pages = 3
    results = []

    for page in range(1, pages + 1):

        retries = 0

        while retries < 3:
            try:

                # simulation erreurs API
                if random.random() < 0.15:
                    raise Exception("429 rate limit")

                if random.random() < 0.10:
                    raise Exception("500 server error")

                results.append({
                    "siren": siren,
                    "page": page,
                    "status": "active",
                    "name": f"Company {siren}"
                })

                break

            except Exception as e:
                retries += 1
                wait = (2 ** retries) + random.random()
                time.sleep(wait)

    return results