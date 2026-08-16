import { differenceInCalendarDays, format, isAfter, isValid, parseISO } from "date-fns";

export function formatDateShort(iso: string): string {
  const date = parseISO(iso);
  if (!isValid(date)) return iso;
  return format(date, "MMM d");
}

export function formatDateRange(startIso: string, endIso: string): string {
  const start = parseISO(startIso);
  const end = parseISO(endIso);
  if (!isValid(start) || !isValid(end)) return `${startIso} – ${endIso}`;
  const sameMonth = start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear();
  const startFmt = format(start, sameMonth ? "MMM d" : "MMM d, yyyy");
  const endFmt = format(end, "MMM d, yyyy");
  return `${startFmt} – ${endFmt}`;
}

export function tripLengthNights(startIso: string, endIso: string): number {
  const start = parseISO(startIso);
  const end = parseISO(endIso);
  if (!isValid(start) || !isValid(end)) return 0;
  return Math.max(0, differenceInCalendarDays(end, start));
}

export function isEndAfterStart(startIso: string, endIso: string): boolean {
  const start = parseISO(startIso);
  const end = parseISO(endIso);
  if (!isValid(start) || !isValid(end)) return false;
  return isAfter(end, start);
}
