import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {beforeEach,expect,it,vi} from 'vitest';
const native=vi.hoisted(()=>({listen:vi.fn(),platform:vi.fn(()=> 'android')}));
vi.mock('@capacitor/core',()=>({Capacitor:{getPlatform:native.platform},registerPlugin:()=>({listen:native.listen})}));
import VoiceInput from './voice-input';
beforeEach(()=>{vi.clearAllMocks();native.platform.mockReturnValue('android')});
it('uses Android native speech and returns the transcript for review',async()=>{
 native.listen.mockResolvedValue({text:'Add one hundred bottles'});const onText=vi.fn();render(<VoiceInput onText={onText}/>);
 fireEvent.change(screen.getByLabelText('Voice language'),{target:{value:'en-IN'}});fireEvent.click(screen.getByRole('button',{name:/Voice input/}));
 await waitFor(()=>expect(onText).toHaveBeenCalledWith('Add one hundred bottles'));expect(native.listen).toHaveBeenCalledWith({language:'en-IN'});
});
it('shows permission denial without sending a command or saving records',async()=>{
 native.listen.mockRejectedValue(new Error('Microphone permission denied'));const onText=vi.fn();render(<VoiceInput onText={onText}/>);fireEvent.click(screen.getByRole('button',{name:/Voice input/}));
 expect(await screen.findByRole('status')).toHaveTextContent('Microphone permission denied');expect(onText).not.toHaveBeenCalled();
});
