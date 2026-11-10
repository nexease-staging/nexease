import {render,screen,fireEvent} from '@testing-library/react';
import {it,expect} from 'vitest';
import {CircleDollarSign} from 'lucide-react';
import StatCard from './stat-card';
it('keeps meaningful financial text and exposes exact value by tap',()=>{
 render(<StatCard label="Receivables" value="₹1.2L" title="₹1,20,000.00" hint="Owed to you" icon={CircleDollarSign}/>);
 expect(screen.getByText('₹1.2L').className).not.toContain('truncate');
 expect(screen.getByText('Owed to you').className).not.toContain('truncate');
 fireEvent.click(screen.getByText('Exact amount'));
 expect(screen.getByText('₹1,20,000.00').closest('details')).toHaveAttribute('open');
});
