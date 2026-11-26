"""Turns an AI proposal into a conversational next step.

The model only extracts values. This module decides, deterministically:
- which NexEase form should open for the entry (and where it lives),
- which required details are still missing, phrased as short questions with quick choices,
- a short reply for the chat thread.

Nothing here writes business data. Forms opened from the assistant save through their normal,
permission-checked services.
"""
import re
from datetime import date

from apps.business.schema import SCHEMAS

from .ai_actions import RECORD_KINDS

# Kinds that only open a prefilled form; there is no one-tap save for them.
FORM_ONLY = {'customer', 'supplier', 'payment_in', 'payment_out'}
FORM_ONLY_PERMISSIONS = {
    'customer': 'customers.create', 'supplier': 'suppliers.create',
    'payment_in': 'invoices.record_payment', 'payment_out': 'bills.record_payment',
}

LABELS = {
    'invoice': 'Sales invoice', 'bill': 'Purchase bill', 'purchase_order': 'Purchase order',
    'expense': 'Expense', 'advance': 'Employee advance', 'product': 'Item', 'category': 'Item category',
    'stock_adjustment': 'Stock adjustment', 'customer': 'Customer', 'supplier': 'Supplier',
    'payment_in': 'Payment received', 'payment_out': 'Payment made', 'employee': 'Employee',
    'site': 'Client site', 'assignment': 'Assignment', 'attendance': 'Monthly pay inputs',
    'timesheet': 'Timesheet', 'leave_request': 'Leave request', 'question': 'Question',
}

# Where each record kind's form lives, so the assistant can open it there.
RECORD_ROUTES = {
    'expenses': '/expenses', 'advances': '/workforce/advances', 'employees': '/workforce/employees',
    'sites': '/workforce/sites', 'assignments': '/workforce/assignments', 'timesheets': '/workforce/timesheets',
    'leave_requests': '/workforce/leave', 'attendance': '/workforce/inputs',
}
FORM_RECORD_KINDS = {**RECORD_KINDS, 'expense': 'expenses', 'advance': 'advances'}

DOCUMENT_KINDS = ('invoice', 'bill', 'purchase_order')
PAYMENT_MODES = ['Cash', 'UPI', 'Bank transfer', 'Card', 'Cheque']
GST_RATES = ['0', '5', '12', '18', '28']

# Fields the form fills on its own (today's date, automatic codes and references).
AUTO_FILLED = {'date', 'reference', 'code', 'status', 'joining_date', 'start_date', 'period_days', 'billable_units', 'billing_rate'}

# Fields in the AI proposal that feed each record form field when the names differ.
RECORD_SOURCE = {'payee': 'party_name'}

QUESTIONS = {
    'party_name': {'invoice': 'Who is the customer?', 'bill': 'Which supplier is this bill from?', 'purchase_order': 'Which supplier is this order for?',
                   'payment_in': 'Who paid you?', 'payment_out': 'Who did you pay?', 'expense': 'Who was it paid to?'},
    'amount': 'How much was it?',
    'payment_mode': 'How was it paid?',
    'name': {'customer': "What is the customer's name?", 'supplier': "What is the supplier's name?", 'product': 'What is the item called?',
             'category': 'What should the category be called?', 'employee': "What is the employee's name?", 'site': 'What is the site called?'},
    'selling_price': 'What is the selling price?',
    'quantity_change': 'How many units to add or remove? Use a minus sign to remove.',
    'product_name': 'Which item is this for?',
    'employee_id': 'Which employee is this for?',
    'category': 'Which expense category fits?',
    'description': 'What was it for?',
    'rate': 'What is the pay rate?',
    'basis': 'Is pay monthly, daily, hourly or per piece?',
    'site_id': 'Which client site?',
    'month': 'Which month (YYYY-MM)?',
    'paid_days': 'How many paid days?',
    'hours': 'How many hours were worked?',
    'leave_type': 'What type of leave?',
    'end_date': 'Until which date?',
    'days': 'How many days?',
    'shift': 'Which shift?',
}


def _question(field, kind, label):
    q = QUESTIONS.get(field)
    if isinstance(q, dict):
        q = q.get(kind)
    return q or 'What is the ' + label.lower() + '?'


def _money(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return ''
    whole, _, frac = ('%.2f' % abs(n)).partition('.')
    # Indian grouping: 12,34,567.89
    head, tail = whole[:-3], whole[-3:]
    if head:
        head = re.sub(r'(\d)(?=(\d\d)+$)', r'\1,', head) + ','
    text = '₹' + head + tail + ('' if frac == '00' else '.' + frac)
    return ('-' if n < 0 else '') + text


def _line_total(line):
    try:
        net = float(line.get('quantity') or 0) * float(line.get('unit_price') or 0) - float(line.get('discount') or 0)
        return net * (1 + float(line.get('tax_rate') or 0) / 100)
    except ValueError:
        return 0.0


def form_for(kind):
    """The form the assistant opens for an entry kind."""
    if kind in DOCUMENT_KINDS:
        return {'type': 'invoice' if kind == 'invoice' else 'purchase', 'route': '/invoices' if kind == 'invoice' else '/vendor-bills' if kind == 'bill' else '/purchase-orders'}
    if kind in ('payment_in', 'payment_out'):
        return {'type': 'payment', 'route': '/payments'}
    if kind in ('customer', 'supplier', 'product', 'stock_adjustment', 'category'):
        return {'type': kind, 'route': {'customer': '/customers', 'supplier': '/suppliers', 'product': '/products', 'stock_adjustment': '/inventory', 'category': '/settings/categories'}[kind]}
    if kind in FORM_RECORD_KINDS:
        record = FORM_RECORD_KINDS[kind]
        return {'type': 'record', 'record_kind': record, 'route': RECORD_ROUTES.get(record)}
    return None


def _missing(kind, f, items):
    out = []

    def need(field, label, required=True, choices=None, input_type='text', **extra):
        out.append({'field': field, 'label': label, 'question': extra.pop('question', None) or _question(field, kind, label),
                    'required': required, 'choices': choices or [], 'input': input_type, **extra})

    if kind in DOCUMENT_KINDS:
        if not f.get('party_name') and not f.get('party_code'):
            need('party_name', 'Customer' if kind == 'invoice' else 'Supplier')
        if not items:
            need('items.0.name', 'Item', question='What did you ' + ('sell' if kind == 'invoice' else 'buy') + '? Item name, quantity and rate is enough.')
        for i, line in enumerate(items):
            name = line.get('name') or line.get('sku') or 'item ' + str(i + 1)
            if not line.get('name') and not line.get('sku'):
                need('items.%d.name' % i, 'Item name', question='What is item %d called?' % (i + 1))
            if not line.get('quantity'):
                need('items.%d.quantity' % i, 'Quantity', input_type='number', question='How many ' + name + '?')
            if not line.get('unit_price'):
                need('items.%d.unit_price' % i, 'Rate', input_type='number', question='What is the rate for ' + name + '?')
            if line.get('tax_rate', '') == '':
                need('items.%d.tax_rate' % i, 'GST %', required=False, choices=GST_RATES, input_type='choice', question='GST rate for ' + name + '?')
        return out
    if kind in ('payment_in', 'payment_out'):
        if not f.get('party_name') and not f.get('party_code'):
            need('party_name', 'Customer' if kind == 'payment_in' else 'Supplier')
        if not f.get('amount'):
            need('amount', 'Amount', input_type='number')
        if not f.get('payment_mode'):
            need('payment_mode', 'Payment mode', choices=PAYMENT_MODES, input_type='choice')
        return out
    if kind in ('customer', 'supplier'):
        if not f.get('name') and not f.get('party_name'):
            need('name', 'Name')
        if not f.get('phone'):
            need('phone', 'Phone', required=False, question='Add a phone number? (optional)')
        if not f.get('party_gstin'):
            need('party_gstin', 'GSTIN', required=False, question='Do they have a GSTIN? (optional)')
        return out
    if kind == 'product':
        if not f.get('name'):
            need('name', 'Item name')
        if not f.get('selling_price'):
            need('selling_price', 'Selling price', input_type='number')
        return out
    if kind == 'category':
        if not f.get('name'):
            need('name', 'Category name')
        return out
    if kind == 'stock_adjustment':
        if not f.get('product_id'):
            need('product_name', 'Item')
        if not f.get('quantity_change'):
            need('quantity_change', 'Quantity change', input_type='number')
        return out
    record = FORM_RECORD_KINDS.get(kind)
    if record:
        for key, spec in SCHEMAS[record]['fields'].items():
            if not spec.get('required') or key in AUTO_FILLED:
                continue
            source = RECORD_SOURCE.get(key, key)
            if f.get(source):
                continue
            if key == 'employee_id' and f.get('employee_name'):
                continue
            if key == 'site_id' and f.get('site_name'):
                continue
            if spec['type'] == 'select' and key not in ('category', 'payment_mode', 'basis', 'leave_type'):
                continue  # the form picks the first option; not worth a question
            choices = spec.get('choices') or []
            need(source, spec.get('label') or key, choices=choices,
                 input_type='choice' if choices else 'number' if spec['type'] == 'number' else 'date' if spec['type'] == 'date' else 'text')
    return out


def _summary(kind, f, items):
    rows = []

    def add(label, value):
        if value:
            rows.append({'label': label, 'value': value})

    if kind in DOCUMENT_KINDS:
        add('Customer' if kind == 'invoice' else 'Supplier', f.get('party_name') or f.get('party_code'))
        add('Date', f.get('date'))
        add('Items', ', '.join(filter(None, ((l.get('name') or l.get('sku')) + (' × ' + l['quantity'] if l.get('quantity') else '') for l in items))))
        total = sum(_line_total(l) for l in items)
        add('Total', _money(f.get('document_total') or (total if total else '')))
    elif kind in ('payment_in', 'payment_out'):
        add('From' if kind == 'payment_in' else 'To', f.get('party_name'))
        add('Amount', _money(f.get('amount')))
        add('Mode', f.get('payment_mode'))
        add('Date', f.get('date'))
    elif kind in ('customer', 'supplier'):
        add('Name', f.get('name') or f.get('party_name'))
        add('Phone', f.get('phone'))
        add('GSTIN', f.get('party_gstin'))
        add('City / address', f.get('party_address') or f.get('address'))
    elif kind == 'stock_adjustment':
        add('Item', f.get('product_name'))
        add('Change', f.get('quantity_change'))
        add('Warehouse', f.get('warehouse_name'))
    elif kind == 'product':
        add('Name', f.get('name'))
        add('Selling price', _money(f.get('selling_price')))
        add('Unit', f.get('unit'))
        add('GST HSN/SAC', f.get('hsn_code'))
    else:
        add('Paid to' if kind == 'expense' else 'Employee' if f.get('employee_name') and not f.get('name') else 'Name', f.get('name') or f.get('employee_name') or f.get('party_name'))
        add('Amount', _money(f.get('amount')) or _money(f.get('rate')))
        add('Category', f.get('category'))
        add('Mode', f.get('payment_mode'))
        add('Date', f.get('date') or f.get('start_date') or f.get('month'))
        add('For', f.get('description'))
    return rows[:6]


def assist(kind, data, warnings=(), refs=None):
    """Conversational view of a proposal: form to open, gaps to ask about, chat reply."""
    data = data or {}
    f = data.get('fields') or {}
    items = data.get('items') or []
    label = LABELS.get(kind, (kind or 'entry').replace('_', ' ').capitalize())
    form = form_for(kind)
    model_questions = [q for q in (data.get('questions') or []) if q]
    if kind == 'question' or not form:
        return {'kind': kind or 'question', 'label': label, 'form': None, 'missing': [], 'ready': False,
                'summary': [], 'refs': refs or {}, 'quick_save': False,
                'reply': ' '.join(model_questions) or 'Tell me what to record, for example: "Invoice Sharma Traders 10 bags cement at 380, 18% GST".'}
    missing = _missing(kind, f, items)
    required = [m for m in missing if m['required']]
    ready = not required and not (kind == 'stock_adjustment' and model_questions)
    summary = _summary(kind, f, items)
    head = summary[0]['value'] if summary else ''
    if required:
        reply = label + (' for ' + head if head else '') + ' — almost there. ' + required[0]['question']
    elif missing:
        reply = label + (' for ' + head if head else '') + ' is ready to open. ' + missing[0]['question']
    else:
        reply = label + (' for ' + head if head else '') + ' is ready. Opening the form with everything filled in — check it and save.'
    # Questions the model raised that the checklist does not already cover.
    extra = [q for q in model_questions if not any(q.strip().lower() == m['question'].lower() for m in missing)]
    return {'kind': kind, 'label': label, 'form': form, 'missing': missing, 'ready': ready, 'summary': summary,
            'reply': reply, 'notes': extra[:3] + [w for w in warnings if w][:3], 'refs': refs or {},
            'quick_save': kind not in FORM_ONLY}


def resolve_refs(org, kind, data):
    """IDs the form needs and the model cannot know (e.g. the party for a payment)."""
    f = (data or {}).get('fields') or {}
    if kind not in ('payment_in', 'payment_out') or not (f.get('party_code') or f.get('party_name')):
        return {}
    from apps.sales.models import Customer
    from apps.purchasing.models import Supplier
    model = Customer if kind == 'payment_in' else Supplier
    q = model.objects(organization=org, is_active=True)
    matches = list(q.filter(code=f['party_code'].upper())) if f.get('party_code') else list(q.filter(name__iexact=f['party_name'].strip()))
    if len(matches) != 1 and f.get('party_name'):
        matches = list(q.filter(name__icontains=f['party_name'].strip()).limit(2))
    if len(matches) == 1:
        f.update(party_name=matches[0].name, party_code=matches[0].code)
        return {'party_id': str(matches[0].id)}
    return {}


# ---- Fast path -----------------------------------------------------------------------------
# A few unambiguous everyday commands are understood instantly, without a model call.

_AMOUNT = r'(?:₹|rs\.?|inr)?\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)\s*(?:/-|rs|rupees?)?'
_MODE = r'(?:\s+(?:(?:by|via|through|in|on|from|se)\s+)?(?P<mode>cash|upi|gpay|phonepe|paytm|bank(?:\s+transfer)?|neft|imps|rtgs|cheque|check|card))?'
_MODES = {'cash': 'Cash', 'upi': 'UPI', 'gpay': 'UPI', 'phonepe': 'UPI', 'paytm': 'UPI', 'bank': 'Bank transfer', 'bank transfer': 'Bank transfer',
          'neft': 'Bank transfer', 'imps': 'Bank transfer', 'rtgs': 'Bank transfer', 'cheque': 'Cheque', 'check': 'Cheque', 'card': 'Card'}
_RECEIVED = [
    re.compile(r'^(?:received|got|receive|collected)\s+' + _AMOUNT + r'\s+from\s+(?P<party>.+?)' + _MODE + r'\s*\.?$', re.I),
    re.compile(r'^(?P<party>.+?)\s+(?:paid me|paid us|ne diye|se mila|se mile|se aaya)\s+' + _AMOUNT + _MODE + r'\s*\.?$', re.I),
    re.compile(r'^(?P<party>.+?)\s+se\s+' + _AMOUNT + r'\s+(?:mila|mile|aaya|aaye|received)' + _MODE + r'\s*\.?$', re.I),
]
_PARTY = re.compile(r'^(?:add|create|new)\s+(?:a\s+)?(?:new\s+)?(?P<kind>customer|client|supplier|vendor)\s+(?P<rest>.+)$', re.I)
_PHONE = re.compile(r'(?:\+91[\s-]?)?(?<!\d)([6-9]\d{9})(?!\d)')
_GSTIN = re.compile(r'\b(\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b', re.I)


def _blank(fields):
    return dict.fromkeys(fields, '')


def quick_intent(text, fields, today=None):
    """Return a proposal dict for simple commands, or None to use the model."""
    text = (text or '').strip()
    if not text or len(text) > 200 or '\n' in text:
        return None
    today = today or date.today().isoformat()
    for pattern in _RECEIVED:
        m = pattern.match(text)
        if m:
            party = re.sub(r'\s+', ' ', m.group('party')).strip(' ,.')
            if not party or len(party) > 80:
                return None
            f = _blank(fields)
            f.update(party_name=party, amount=m.group('amount').replace(',', ''), date=today,
                     payment_mode=_MODES.get((m.group('mode') or '').lower(), ''))
            return {'kind': 'payment_in', 'fields': f, 'items': [], 'questions': [], 'warnings': []}
    m = _PARTY.match(text)
    if m:
        rest = m.group('rest')
        f = _blank(fields)
        phone = _PHONE.search(rest)
        gstin = _GSTIN.search(rest)
        if phone:
            f['phone'] = phone.group(1)
            rest = rest.replace(phone.group(0), ' ')
        if gstin:
            f['party_gstin'] = gstin.group(1).upper()
            rest = rest.replace(gstin.group(0), ' ')
        city = re.search(r'\s(?:from|in|at|,)\s*([A-Za-z][A-Za-z .]{1,40})$', ' ' + rest.strip())
        if city:
            f['party_address'] = city.group(1).strip()
            rest = (' ' + rest.strip())[:city.start()]
        name = re.sub(r'\b(?:named|called|phone|mobile|gstin|gst|number|no\.?)\b', ' ', rest, flags=re.I)
        name = re.sub(r'\s+', ' ', name).strip(' ,.:-')
        if not name or len(name) > 80:
            return None
        f['name'] = f['party_name'] = name
        kind = 'customer' if m.group('kind').lower() in ('customer', 'client') else 'supplier'
        return {'kind': kind, 'fields': f, 'items': [], 'questions': [], 'warnings': []}
    return None
