import logging
from time import perf_counter
from apps.core.services.request_performance import begin, finish

logger = logging.getLogger('ims')


class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = begin(request.method)
        start = perf_counter()
        response = None
        try:
            response = self.get_response(request)
            return response
        finally:
            elapsed = (perf_counter() - start) * 1000
            state = finish(token)
            if response is not None:
                response['Server-Timing'] = (
                    f'app;dur={elapsed:.2f}, mongo;dur={state["mongo_ms"]:.2f};'
                    f'desc="{state["mongo_commands"]} commands"'
                )
            logger.info(
                'NexEase request timing | request_id=%s | method=%s | path=%s | '
                'duration_ms=%.2f | mongo_commands=%s | mongo_ms=%.2f',
                getattr(request, 'request_id', '-'), request.method, request.path,
                elapsed, state['mongo_commands'], state['mongo_ms'],
            )
