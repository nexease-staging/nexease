"use client";
import { forwardRef, useState, type InputHTMLAttributes } from 'react';
import { Eye, EyeOff } from 'lucide-react';

const PasswordInput = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function PasswordInput({ type = 'password', className = '', ...props }, ref) {
  const [visible, setVisible] = useState(false);
  if (type !== 'password') return <input ref={ref} type={type} className={className} {...props}/>;
  return <span className="nx-password-field">
    <input {...props} ref={ref} type={visible ? 'text' : 'password'} className={className + ' nx-password-input'}/>
    <button type="button" className="nx-password-toggle" aria-label={visible ? 'Hide password' : 'Show password'} aria-pressed={visible} aria-controls={props.id} disabled={props.disabled} onClick={() => setVisible(v => !v)}>
      {visible ? <EyeOff size={18} aria-hidden="true"/> : <Eye size={18} aria-hidden="true"/>}
    </button>
  </span>;
});
export default PasswordInput;
