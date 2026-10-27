import os

from mongoengine import connect


def connect_to_mongodb():

    uri = os.getenv(
        "MONGODB_URI"
    )

    database = os.getenv(
        "MONGODB_DATABASE"
    )

    if not uri:
        raise ValueError(
            "MONGODB_URI is not configured."
        )

    if not database:
        raise ValueError(
            "MONGODB_DATABASE is not configured."
        )

    return connect(
        db=database,
        host=uri,

        # Retry supported read operations.
        retryReads=True,

        # Retry supported write operations.
        retryWrites=True,

        # Do not retain idle sockets indefinitely.
        maxIdleTimeMS=60000,

        # Connection establishment timeout.
        connectTimeoutMS=30000,

        # Server selection timeout.
        serverSelectionTimeoutMS=30000,

        # Socket operation timeout.
        socketTimeoutMS=60000,
    )