class BackgroundJobExecutor:

    _handlers = {}

    @classmethod
    def register(
        cls,
        job_type,
        handler,
    ):
        job_type = (
            str(job_type or "")
            .strip()
            .upper()
        )

        if not job_type:
            raise ValueError(
                "Job type is required."
            )

        if not callable(handler):
            raise ValueError(
                "Background job handler "
                "must be callable."
            )

        if job_type in cls._handlers:
            raise ValueError(
                f"Handler already registered "
                f"for job type: {job_type}."
            )

        cls._handlers[job_type] = handler

    @classmethod
    def get_handler(
        cls,
        job_type,
    ):
        job_type = (
            str(job_type or "")
            .strip()
            .upper()
        )

        handler = cls._handlers.get(
            job_type
        )

        if handler is None:
            raise ValueError(
                f"No background job handler "
                f"registered for: {job_type}."
            )

        return handler

    @classmethod
    def execute(
        cls,
        *,
        job,
    ):
        if job is None:
            raise ValueError(
                "Background job is required."
            )

        handler = cls.get_handler(
            job.job_type
        )

        return handler(
            job=job,
        )

    @classmethod
    def registered_job_types(cls):
        return tuple(
            sorted(
                cls._handlers.keys()
            )
        )

    @classmethod
    def clear(cls):
        cls._handlers.clear()