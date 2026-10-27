"""Tenant-scoped automatic journals. Source records remain the audit authority.
Deterministic journal numbers make retries safe after an interrupted save.
"""
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from mongoengine.errors import NotUniqueError
from apps.finance.models import ChartOfAccount,JournalEntry,JournalLine
from apps.finance.services.chart_of_account_service import ChartOfAccountService
from .payroll import amount,money

EXTRA=[('1450','Employee advances','ASSET','EMPLOYEE_ADVANCES'),('2200','Salary payable','LIABILITY','SALARY_PAYABLE'),('2210','Payroll deductions payable','LIABILITY','PAYROLL_DEDUCTIONS'),('5100','Wages and salaries','EXPENSE','PAYROLL_EXPENSE'),('5110','Employer contributions','EXPENSE','EMPLOYER_CONTRIBUTIONS'),('5200','Utilities','EXPENSE','EXP_UTILITIES'),('5210','Travel','EXPENSE','EXP_TRAVEL'),('5220','Petrol and fuel','EXPENSE','EXP_FUEL'),('5230','Rent','EXPENSE','EXP_RENT'),('5240','Office supplies','EXPENSE','EXP_OFFICE'),('5250','Repairs and maintenance','EXPENSE','EXP_REPAIRS'),('5260','Meals','EXPENSE','EXP_MEALS'),('5270','Other daily expenses','EXPENSE','EXP_OTHER'),('2220','Credit card payable','LIABILITY','CREDIT_CARD_PAYABLE')]
CATEGORIES={'Utilities':'EXP_UTILITIES','Travel':'EXP_TRAVEL','Petrol / fuel':'EXP_FUEL','Rent':'EXP_RENT','Office supplies':'EXP_OFFICE','Repairs / maintenance':'EXP_REPAIRS','Meals':'EXP_MEALS','Other':'EXP_OTHER'}
MODES=['Cash','Bank transfer','UPI','Debit card','Credit card']

def ensure_accounts(org,user):
    defaults=[dict(d) for d in ChartOfAccountService.DEFAULT_ACCOUNTS]
    defaults += [dict(account_code=c,account_name=n,account_type=t,account_subtype='CURRENT_ASSET' if t=='ASSET' else 'CURRENT_LIABILITY' if t=='LIABILITY' else 'OPERATING_EXPENSE',normal_balance='DEBIT' if t in ('ASSET','EXPENSE') else 'CREDIT',system_key=k,description='NexEase automatic business posting',is_system_account=True,allow_manual_posting=False) for c,n,t,k in [(f'NX-{i+1:03}',n,t,k) for i,(c,n,t,k) in enumerate(EXTRA)]]
    for d in defaults:
        a=ChartOfAccount.objects(organization=org,system_key=d['system_key']).first() if d['system_key'] else None
        if a:
            if not a.is_active:raise ValueError('System account is inactive: '+d['system_key']+'. Ask your accountant to review it.')
            if a.account_type!=d['account_type']:raise ValueError('System account type mismatch: '+d['system_key'])
            continue
        existing=ChartOfAccount.objects(organization=org,account_code=d['account_code']).first()
        if existing:
            if existing.system_key!=d['system_key']:raise ValueError('Account code '+d['account_code']+' is already used. Review the chart of accounts before setup.')
            continue
        try:ChartOfAccount(organization=org,created_by=user,**d).save()
        except NotUniqueError:
            a=ChartOfAccount.objects(organization=org,account_code=d['account_code']).first()
            if not a or a.system_key!=d['system_key'] or not a.is_active:raise ValueError('Concurrent account setup conflict. Reload and review the chart.')

def account(org,key):
    a=ChartOfAccount.objects(organization=org,system_key=key,is_active=True).first()
    if not a:raise ValueError('Missing active account: '+key)
    return a

def payment_account(org,mode,selected=''):
    if mode not in MODES:raise ValueError('Select a payment mode.')
    key='CASH' if mode=='Cash' else 'CREDIT_CARD_PAYABLE' if mode=='Credit card' else 'BANK'
    if selected:
        a=ChartOfAccount.objects(id=selected,organization=org,is_active=True).first()
        if not a or a.account_type!=('LIABILITY' if mode=='Credit card' else 'ASSET'):raise ValueError('Choose an active payment account of the correct type in this organisation.')
        return a
    return account(org,key)

def post(org,user,kind,source,when,description,entries):
    number='NX-'+sha256((str(org.id)+':'+kind+':'+source).encode()).hexdigest()[:28].upper()
    lines=[JournalLine(account=a,debit=Decimal(money(amount(dr))),credit=Decimal(money(amount(cr))),description=description[:500]) for a,dr,cr in entries if amount(dr) or amount(cr)]
    debit=sum((l.debit for l in lines),Decimal(0));credit=sum((l.credit for l in lines),Decimal(0))
    if not lines:return None
    if debit!=credit or debit<=0:raise ValueError('Automatic journal is not balanced.')
    for l in lines:
        if l.account.organization.id!=org.id or not l.account.is_active or (l.debit and l.credit):raise ValueError('Invalid journal account or line.')
    old=JournalEntry.objects(organization=org,journal_number=number).first()
    if old:
        expected=[(str(l.account.id),l.debit,l.credit) for l in lines]
        actual=[(str(l.account.id),l.debit,l.credit) for l in old.lines]
        if old.status!='POSTED' or actual!=expected:raise ValueError('Existing journal differs from source. Accountant review required: '+number)
        return old
    if isinstance(when,str):when=datetime.fromisoformat(when)
    try:return JournalEntry(organization=org,journal_number=number,journal_date=when,description=description,source_type=kind,source_id=source,lines=lines,total_debit=debit,total_credit=credit,status='POSTED',posted_at=datetime.utcnow(),created_by=user).save()
    except NotUniqueError:return post(org,user,kind,source,when,description,entries)

def sync_record(record,user):
    org=record.organization;d=record.data;ensure_accounts(org,user);key=str(record.id);result=[]
    if record.kind=='expenses':
        value=amount(d['amount']);result.append(post(org,user,'DAILY_EXPENSE',key,d['date'],d['category']+': '+d['description'],[(account(org,CATEGORIES[d['category']]),value,0),(payment_account(org,d['payment_mode'],d.get('payment_account','')),0,value)]))
    elif record.kind=='advances':
        # Historical records with opening recoveries need an accountant's opening balance, not a fabricated cash movement.
        if amount(d.get('recovered',0)):raise ValueError('An opening advance with prior recoveries needs a reviewed opening journal.')
        result.append(post(org,user,'EMPLOYEE_ADVANCE',key,d['date'],'Employee advance '+d['reference'],[(account(org,'EMPLOYEE_ADVANCES'),d['amount'],0),(payment_account(org,d.get('payment_mode') or 'Bank transfer',d.get('payment_account','')),0,d['amount'])]))
    elif record.kind=='payruns' and d['status'] in ('approved','paid'):
        from .automation import bounds
        totals={k:sum((amount(r['result'].get(k,0)) for r in d['rows']),Decimal(0)) for k in ['gross','net','deductions','employer_pf','employer_esi']}
        recovery=sum((amount(r['inputs'].get('advance_recovery',0)) for r in d['rows']),Decimal(0));employer=totals['employer_pf']+totals['employer_esi']
        entries=[(account(org,'PAYROLL_EXPENSE'),totals['gross'],0),(account(org,'EMPLOYER_CONTRIBUTIONS'),employer,0),(account(org,'SALARY_PAYABLE'),0,totals['net']),(account(org,'EMPLOYEE_ADVANCES'),0,recovery),(account(org,'PAYROLL_DEDUCTIONS'),0,totals['deductions']-recovery+employer)]
        result.append(post(org,user,'PAYROLL',key,bounds(record.key)[1].isoformat(),'Payroll '+record.key,entries))
        for p in d.get('payments',[]):
            result.append(post(org,user,'SALARY_PAYMENT',key+':'+sha256((p['employee_id']+':'+p['reference']).encode()).hexdigest()[:24],p['date'],'Salary payment '+p['reference'],[(account(org,'SALARY_PAYABLE'),p['amount'],0),(payment_account(org,p.get('payment_mode') or 'Bank transfer',p.get('payment_account','')),0,p['amount'])]))
    return [str(j.id) for j in result if j]
