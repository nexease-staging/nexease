import {expect,it} from 'vitest';
import {discountAmount,discountedPayload} from './discount';
const line={quantity:"3",unit_price:"100",discount:"10"};
it('calculates percentage on the full line value',()=>expect(discountAmount({...line,discount_mode:"percent"})).toBe("30.00"));
it('keeps rupee discounts as a line amount',()=>expect(discountAmount(line)).toBe("10.00"));
it('rounds fractional paise half up without floating point drift',()=>expect(discountAmount({quantity:"1",unit_price:"0.05",discount:"10",discount_mode:"percent"})).toBe("0.01"));
it('rejects invalid and excessive discounts',()=>{
 for(const discount of ["-1","101","Infinity"])expect(()=>discountAmount({...line,discount,discount_mode:"percent"})).toThrow();
 expect(()=>discountAmount({...line,discount:"301"})).toThrow();
});
it('sends a compatible amount payload without the UI-only mode',()=>expect(discountedPayload({...line,discount_mode:"percent"})).toEqual({...line,discount:"30.00"}));
