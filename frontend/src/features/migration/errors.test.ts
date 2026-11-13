import {describe,expect,it} from 'vitest';
import {migrationErrorMessage} from './errors';
describe('migration error feedback',()=>{
 it('keeps field reasons from rejected API requests',()=>{
  const error=Object.assign(new Error('Migration validation failed.'),{details:{migration_type:['Unsupported migration type.'],file:['Only CSV and XLSX migration files are supported.']}});
  expect(migrationErrorMessage(error,'Failed')).toContain('migration_type: Unsupported migration type.');
  expect(migrationErrorMessage(error,'Failed')).toContain('file: Only CSV and XLSX');
 });
 it('handles plain errors and absent details',()=>{
  expect(migrationErrorMessage(new Error('File is empty.'),'Failed')).toBe('File is empty.');
  expect(migrationErrorMessage(null,'Failed')).toBe('Failed');
 });
});
