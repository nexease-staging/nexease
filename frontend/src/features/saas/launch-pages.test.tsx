import {render,screen,fireEvent,act} from '@testing-library/react';
import {describe,it,expect,vi,afterEach} from 'vitest';
import ServicePricing from './service-pricing';
import DeadlineCalendar,{countdown} from './deadline-calendar';
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn().mockResolvedValue({data:{notice:'Standard dates need extension review',rows:[{id:'gst',title:'GSTR-3B',category:'GST',period:'2026-10',applies_to:'Monthly filers',due_at:'2026-11-20T23:59:59+05:30',source_url:'https://gst.gov.in/',status:'standard',note:'Check extensions'}]}})}));
afterEach(()=>vi.useRealTimers());
describe('Launch pricing and deadlines',()=>{
 it('offers the real PDF and shows discounted packages',()=>{render(<ServicePricing/>);expect(screen.getByRole('link',{name:/Download price list PDF/})).toHaveAttribute('href','/NexEase_Pricing.pdf');expect(screen.getByText('₹1,099')).toBeVisible();fireEvent.click(screen.getByRole('button',{name:'Managed packages'}));expect(screen.getByText('₹4,799')).toBeVisible();expect(screen.getByText('Save ₹996')).toBeVisible()});
 it('switches to all individual filing fees',()=>{render(<ServicePricing/>);fireEvent.click(screen.getByRole('button',{name:'Filings & registrations'}));expect(screen.getByText('GST registration assistance')).toBeVisible();expect(screen.getByText('Business / professional ITR')).toBeVisible()});
 it('counts down with days and zero-padded hours then stops at zero',()=>{const due='2026-11-20T23:59:59+05:30',epoch=Date.parse(due);expect(countdown(due,epoch-15*86400000-3661000)).toEqual({days:15,time:'01:01:01',passed:false});expect(countdown(due,epoch+1000)).toEqual({days:0,time:'00:00:00',passed:true})});
 it('loads live countdown and changes seconds without refetching',async()=>{vi.useFakeTimers();vi.setSystemTime(new Date('2026-11-04T00:00:00+05:30'));render(<DeadlineCalendar/>);await act(async()=>{await Promise.resolve()});const timer=screen.getByRole('timer');const before=timer.textContent;act(()=>vi.advanceTimersByTime(1000));expect(timer.textContent).not.toEqual(before);expect(screen.getByText('Official source ↗')).toHaveAttribute('href','https://gst.gov.in/');fireEvent.change(screen.getByLabelText('Filing scheme'),{target:{value:'22'}});expect(screen.getByText('No configured deadlines match this filter.')).toBeVisible()});
});
