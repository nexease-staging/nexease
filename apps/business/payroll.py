"""Decimal-based configurable payroll; statutory eligibility is an explicit input."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_CEILING

def amount(value, label='Amount', maximum='1000000000'):
    try: n=Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError): raise ValueError(f'{label} must be a number.')
    if not n.is_finite() or n < 0 or n > Decimal(maximum): raise ValueError(f'{label} is out of range.')
    return n

def money(n): return str(n.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))

def calculate(employee, attendance, policy):
    rate=amount(employee['rate'],'Pay rate')
    basis=employee['basis']
    days=amount(attendance.get('paid_days',0),'Paid days','31')
    period=amount(attendance.get('period_days',30),'Period days','31')
    if period < 1 or days > period: raise ValueError('Paid days cannot exceed period days.')
    units=amount(attendance.get('units',0),'Units')
    hours=amount(attendance.get('hours',0),'Hours','744')
    if basis=='monthly': base=rate*days/period
    elif basis=='daily': base=rate*days
    elif basis=='hourly': base=rate*hours
    elif basis=='piece': base=rate*units
    else: raise ValueError('Unknown pay basis.')
    overtime=amount(attendance.get('overtime_hours',0),'Overtime hours','744')*amount(employee.get('overtime_rate',0),'Overtime rate')
    additions=sum(amount(attendance.get(k,0),k) for k in ['allowances','bonus','arrears'])
    gross=base+overtime+additions
    pf_wages=amount(attendance.get('pf_wages',0),'PF wages')
    esi_wages=amount(attendance.get('esi_wages',0),'ESI wages')
    if pf_wages>gross or esi_wages>gross:raise ValueError('Contribution wages cannot exceed gross earnings.')
    pf=employer_pf=esi=employer_esi=Decimal(0)
    if employee.get('pf_member'):
        if not policy.get('confirmed'):raise ValueError('Confirm the applicable contribution policy before running payroll.')
        cap=amount(policy.get('pf_cap',0),'PF wage cap')
        pf_base=min(pf_wages,cap) if cap else pf_wages
        pf=pf_base*amount(policy.get('pf_employee_rate',0),'PF rate','100')/100
        employer_pf=pf_base*amount(policy.get('pf_employer_rate',0),'Employer PF rate','100')/100
    if employee.get('esi_member'):
        if not policy.get('confirmed'):raise ValueError('Confirm the applicable contribution policy before running payroll.')
        if not attendance.get('esi_employee_exempt',False):
            esi=(esi_wages*amount(policy.get('esi_employee_rate',0),'ESI rate','100')/100).quantize(Decimal('1'),rounding=ROUND_CEILING)
        employer_esi=(esi_wages*amount(policy.get('esi_employer_rate',0),'Employer ESI rate','100')/100).quantize(Decimal('1'),rounding=ROUND_CEILING)
    deductions=sum(amount(attendance.get(k,0),k) for k in ['tds','professional_tax','lwf','advance_recovery','other_deductions'])+Decimal(money(pf))+esi
    gross=Decimal(money(gross))
    if deductions>gross: raise ValueError('Deductions exceed earnings; review this employee.')
    return {k:money(v) for k,v in dict(base=base,overtime=overtime,additions=additions,gross=gross,pf=pf,employer_pf=employer_pf,esi=esi,employer_esi=employer_esi,deductions=deductions,net=gross-deductions,employer_cost=gross+employer_pf+employer_esi).items()}
