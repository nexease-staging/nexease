"""Request-local metrics and read memoization; never retains state between requests."""
from contextvars import ContextVar
from pymongo.monitoring import CommandListener

_state = ContextVar('nexease_request_performance', default=None)


def current_scope():
    return _state.get()


def begin(method):
    return _state.set({'read_only': method in ('GET', 'HEAD'), 'cache': {}, 'mongo_commands': 0, 'mongo_ms': 0.0})


def finish(token):
    state = _state.get()
    _state.reset(token)
    return state


def read_once(key, loader):
    state = _state.get()
    if state is None or not state['read_only']:
        return loader()
    if key not in state['cache']:
        state['cache'][key] = loader()
    return state['cache'][key]


class RequestMongoListener(CommandListener):
    # Command documents, filters, connection strings and results are never inspected.
    def started(self, event):
        state = _state.get()
        if state is not None:
            state['mongo_commands'] += 1

    def _completed(self, event):
        state = _state.get()
        if state is not None:
            state['mongo_ms'] += event.duration_micros / 1000

    def succeeded(self, event):
        self._completed(event)

    def failed(self, event):
        self._completed(event)
