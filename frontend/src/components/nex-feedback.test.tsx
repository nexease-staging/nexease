import {render,screen,fireEvent,act} from '@testing-library/react';
import {describe,it,expect,vi,beforeAll} from 'vitest';
import Feedback,{confirmAction,notify} from './nex-feedback';
beforeAll(()=>{HTMLDialogElement.prototype.showModal=vi.fn(function(this:HTMLDialogElement){this.setAttribute('open','')});HTMLDialogElement.prototype.close=vi.fn(function(this:HTMLDialogElement){this.removeAttribute('open')})});
describe('NexEase feedback',()=>{
 it('requires an explicit confirmation',async()=>{render(<Feedback/>);let result!:Promise<boolean>;act(()=>{result=confirmAction('Post this entry?')});expect(screen.getByRole('dialog')).toHaveAttribute('open');fireEvent.click(screen.getByText('Cancel'));expect(await result).toBe(false)});
 it('confirms and queues feedback',async()=>{render(<Feedback/>);let result!:Promise<boolean>;act(()=>{result=confirmAction('Continue?');notify('Saved')});fireEvent.click(screen.getByText('Confirm'));expect(await result).toBe(true);expect(screen.getByText('Saved')).toBeVisible();fireEvent.click(screen.getByText('Okay'));expect(screen.queryByRole('dialog')).toBeNull()});
});
