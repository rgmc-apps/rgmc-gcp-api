"""BigQuery reads with an enforced wall-clock timeout.

pandas_gbq.read_gbq has no timeout parameter of its own, and google-api-core's default
retry policy for transient errors (the class of error a flaky SSL connection to
bigquery.googleapis.com raises) has a 600-second deadline baked in -- confirmed live:
a GET /bigquery_routes/by_table/value call failed after exactly 600.0s with
"SSLError(SSLEOFError(...))" inside google-api-core's retry loop, tying up the
Cloud Run instance handling it for the full 10 minutes even though the caller
(sbic-manual-trigger-page) had already given up and moved on long before that.

read_gbq_with_timeout runs the read in a worker thread and bounds how long the calling
request waits via Future.result(timeout=...), regardless of what pandas_gbq/
google-api-core are doing internally. This is a wall-clock cutoff on the CALLING code's
wait, not a cancellation of the underlying HTTP call -- Python threads can't be killed
outright, so the background read may keep running briefly after this raises, but the
request that would otherwise have blocked an entire Cloud Run worker for up to 600s now
fails fast and predictably instead.
"""
import concurrent.futures
import os

import pandas_gbq

BQ_READ_TIMEOUT_SECONDS = float(os.getenv("BQ_READ_TIMEOUT_SECONDS", "60"))

# A handful of workers is enough -- this only needs to outlive the occasional stuck
# call long enough to time it out and report back; it isn't meant to add parallelism.
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=8, thread_name_prefix="bq-read")


def read_gbq_with_timeout(*args, timeout: float = BQ_READ_TIMEOUT_SECONDS, **kwargs):
    """Same call shape as pandas_gbq.read_gbq, but raises TimeoutError instead of
    blocking past `timeout` seconds."""
    future = _executor.submit(pandas_gbq.read_gbq, *args, **kwargs)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        raise TimeoutError(f"BigQuery read timed out after {timeout:.0f}s") from None
