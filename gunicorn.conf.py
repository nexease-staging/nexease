import os


# ==================================================
# BIND
# ==================================================

bind = (
    "0.0.0.0:"
    +
    os.getenv(
        "PORT",
        "8000",
    )
)


# ==================================================
# WORKERS
# ==================================================

workers = int(
    os.getenv(
        "WEB_CONCURRENCY",
        "2",
    )
)


worker_class = (
    "sync"
)


threads = int(
    os.getenv(
        "GUNICORN_THREADS",
        "2",
    )
)


# ==================================================
# TIMEOUTS
# ==================================================

timeout = int(
    os.getenv(
        "REQUEST_TIMEOUT_SECONDS",
        "30",
    )
)


graceful_timeout = int(
    os.getenv(
        "GUNICORN_GRACEFUL_TIMEOUT",
        "30",
    )
)


keepalive = int(
    os.getenv(
        "GUNICORN_KEEPALIVE",
        "5",
    )
)


# ==================================================
# WORKER RECYCLING
# ==================================================
#
# Helps limit long-lived memory growth.
# The jitter prevents every worker recycling
# at the same instant.
# ==================================================

max_requests = int(
    os.getenv(
        "GUNICORN_MAX_REQUESTS",
        "1000",
    )
)


max_requests_jitter = int(
    os.getenv(
        "GUNICORN_MAX_REQUESTS_JITTER",
        "100",
    )
)


# ==================================================
# LOGGING
# ==================================================
#
# '-' means stdout / stderr, which is ideal
# for Render and containerized deployments.
# ==================================================

accesslog = "-"

errorlog = "-"


loglevel = (
    os.getenv(
        "GUNICORN_LOG_LEVEL",
        "info",
    )
    .strip()
    .lower()
)


capture_output = True


# ==================================================
# FORWARDED HTTPS
# ==================================================
#
# Django itself already controls whether
# X-Forwarded-Proto is trusted through:
#
# TRUST_PROXY_SSL_HEADER
# SECURE_PROXY_SSL_HEADER
#
# Do not duplicate that trust logic here.
# ==================================================


# ==================================================
# PROCESS
# ==================================================

preload_app = False


# ==================================================
# VALIDATION
# ==================================================

if workers < 1:

    raise ValueError(
        "WEB_CONCURRENCY must be "
        "greater than zero."
    )


if threads < 1:

    raise ValueError(
        "GUNICORN_THREADS must be "
        "greater than zero."
    )


if timeout < 1:

    raise ValueError(
        "REQUEST_TIMEOUT_SECONDS must "
        "be greater than zero."
    )


if graceful_timeout < 1:

    raise ValueError(
        "GUNICORN_GRACEFUL_TIMEOUT must "
        "be greater than zero."
    )


if keepalive < 1:

    raise ValueError(
        "GUNICORN_KEEPALIVE must be "
        "greater than zero."
    )


if max_requests < 1:

    raise ValueError(
        "GUNICORN_MAX_REQUESTS must be "
        "greater than zero."
    )


if max_requests_jitter < 0:

    raise ValueError(
        "GUNICORN_MAX_REQUESTS_JITTER "
        "cannot be negative."
    )