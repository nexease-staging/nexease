import {describe,it,expect} from 'vitest';
import {isInvoiceOverdue} from './format';
describe('IST overdue boundary',()=>{
 const invoice={status:'PARTIALLY_PAID',due_date:'2026-03-31',balance_due:'0.01'};
 it('preserves due-day grace until midnight IST',()=>{
  expect(isInvoiceOverdue(invoice,new Date('2026-03-31T18:29:59Z'))).toBe(false);
  expect(isInvoiceOverdue(invoice,new Date('2026-03-31T18:30:00Z'))).toBe(true);
 });
 it('does not label paid or zero balance as overdue',()=>{
  expect(isInvoiceOverdue({...invoice,status:'PAID'},new Date('2026-04-02'))).toBe(false);
  expect(isInvoiceOverdue({...invoice,balance_due:'0'},new Date('2026-04-02'))).toBe(false);
 });
});
