import {afterEach,describe,expect,it,vi} from 'vitest';
import {dismissTopOverlay} from './overlay-back';
afterEach(()=>{document.body.innerHTML='';});
describe('Android overlay dismissal',()=>{
 it('lets a busy dialog prevent Back without navigating',()=>{
  const dialog=document.createElement('dialog');dialog.open=true;document.body.append(dialog);
  dialog.close=vi.fn();dialog.addEventListener('cancel',event=>event.preventDefault());
  expect(dismissTopOverlay()).toBe(true);expect(dialog.close).not.toHaveBeenCalled();
 });
 it('closes only the last open dialog',()=>{
  const first=document.createElement('dialog'),last=document.createElement('dialog');
  for(const dialog of [first,last]){dialog.open=true;dialog.close=vi.fn();document.body.append(dialog);}
  expect(dismissTopOverlay()).toBe(true);expect(last.close).toHaveBeenCalledOnce();expect(first.close).not.toHaveBeenCalled();
 });
 it('dismisses legacy dialogs using their Close dialog control',()=>{
  document.body.innerHTML='<div role="dialog"><button aria-label="Close dialog">Close</button></div>';
  const button=document.querySelector('button')!;
  button.getBoundingClientRect=()=>({width:44,height:44,left:0,right:44,top:0,bottom:44,x:0,y:0,toJSON:()=>({})});
  const click=vi.fn();button.addEventListener('click',click);
  expect(dismissTopOverlay()).toBe(true);expect(click).toHaveBeenCalledOnce();
 });
 it('allows navigation when no overlay is open',()=>{expect(dismissTopOverlay()).toBe(false);});
});
