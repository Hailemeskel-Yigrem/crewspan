import { FormField } from './FormField';

export interface DateRange {
  start: string;
  end: string;
}

interface DateRangePickerProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  label?: string;
}

export function DateRangePicker({ value, onChange, label = 'Date range' }: DateRangePickerProps) {
  return (
    <div className="date-range-picker">
      <FormField label={`${label} — start`} htmlFor="range-start">
        <input id="range-start" type="date" value={value.start} onChange={(e) => onChange({ ...value, start: e.target.value })} />
      </FormField>
      <FormField label={`${label} — end`} htmlFor="range-end">
        <input id="range-end" type="date" value={value.end} min={value.start} onChange={(e) => onChange({ ...value, end: e.target.value })} />
      </FormField>
      <style>{`.date-range-picker { display: flex; gap: 1rem; flex-wrap: wrap; }`}</style>
    </div>
  );
}
