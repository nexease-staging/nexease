# Worker retry hotfix — 2 November 2026

The worker selects only id, status and available_at for due retry jobs. The old repository requeue method called save() on that partial document, causing required-field validation errors even when the stored job was complete.

Requeue now atomically updates status and updated_at only if the stored job is still RETRYING and due. It preserves payload, organization, creator, idempotency key, attempts and error history. A stale worker cannot reset an already claimed or rescheduled job. No database deletion or migration is required.

## Install

Stop the worker with Ctrl+C. From this ZIP copy `NexEase/apps/core/repositories/background_job_repository.py` over `E:\NexEase\apps\core\repositories\background_job_repository.py`. The accompanying updated regression tests are in `apps/core/tests_background_job_repository.py`.

Keep your existing .env and frontend/.env.local. Restart:

```powershell
Set-Location E:\NexEase
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py run_background_worker
```

Queued work can resume when the worker starts. Inspect Document Logs before manually resending documents. This fix addresses requeueing; an underlying SMTP/authentication error can still cause a delivery to retry or fail.

## Verification

49 backend tests passed across repository, worker command, job service and concurrency suites using an isolated mongomock database. New cases cover the real projected retry query, preservation of job metadata, an already claimed job and a rescheduled job. No live database or SMTP delivery was tested.
