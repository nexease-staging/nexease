import {renderHook,act} from '@testing-library/react';
import {beforeEach,expect,it,vi} from 'vitest';
import {useFormExitGuard} from './use-form-exit-guard';
import {confirmAction} from './nex-feedback';
vi.mock('./nex-feedback',()=>({confirmAction:vi.fn()}));
beforeEach(()=>vi.clearAllMocks());
it('closes unchanged forms without asking',async()=>{
 const close=vi.fn();const {result}=renderHook(()=>useFormExitGuard(false,false,close));
 await act(()=>result.current());expect(close).toHaveBeenCalledOnce();expect(confirmAction).not.toHaveBeenCalled();
});
it('keeps changed forms when discard is cancelled',async()=>{
 vi.mocked(confirmAction).mockResolvedValue(false);const close=vi.fn();
 const {result}=renderHook(()=>useFormExitGuard(true,false,close));
 await act(()=>result.current());expect(close).not.toHaveBeenCalled();
});
it('blocks closing while saving',async()=>{
 const close=vi.fn();const {result}=renderHook(()=>useFormExitGuard(true,true,close));
 await act(()=>result.current());expect(close).not.toHaveBeenCalled();expect(confirmAction).not.toHaveBeenCalled();
});
it('does not queue multiple confirmations for repeated Back presses',async()=>{
 let finish!:(value:boolean)=>void;vi.mocked(confirmAction).mockImplementation(()=>new Promise(resolve=>{finish=resolve;}));
 const close=vi.fn();const {result}=renderHook(()=>useFormExitGuard(true,false,close));
 let pending!:Promise<void>;act(()=>{pending=result.current();void result.current();});
 expect(confirmAction).toHaveBeenCalledOnce();await act(async()=>{finish(true);await pending;});expect(close).toHaveBeenCalledOnce();
});
