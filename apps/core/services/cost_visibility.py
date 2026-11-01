"""Product master cost visibility; purchase/ledger access has separate permissions."""
from apps.authorization.services import AuthorizationService

def can_read_cost(user):
    return bool(user and AuthorizationService.has_permission(user, 'products.read_cost'))

def redact_costs(data):
    if isinstance(data, dict):
        return {k:redact_costs(v) for k,v in data.items() if k != 'cost_price'}
    if isinstance(data, list):
        return [redact_costs(v) for v in data]
    return data
