import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import PasswordInput from './password-input';
it('shows and hides a password without submitting or changing its value',()=>{
 const submit=vi.fn();render(<form onSubmit={submit}><label htmlFor="secret">Password</label><PasswordInput id="secret" defaultValue="private-value"/></form>);
 const input=screen.getByLabelText('Password');expect(input).toHaveAttribute('type','password');
 fireEvent.click(screen.getByRole('button',{name:'Show password'}));expect(input).toHaveAttribute('type','text');expect(input).toHaveValue('private-value');
 fireEvent.click(screen.getByRole('button',{name:'Hide password'}));expect(input).toHaveAttribute('type','password');expect(submit).not.toHaveBeenCalled();
});
it('respects disabled fields and leaves non-password fields unchanged',()=>{
 render(<><PasswordInput disabled aria-label="Secret"/><PasswordInput type="email" aria-label="Email"/></>);
 expect(screen.getByRole('button',{name:'Show password'})).toBeDisabled();expect(screen.getByLabelText('Email')).toHaveAttribute('type','email');
});
