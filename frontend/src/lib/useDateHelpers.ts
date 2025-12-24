// src/composables/useDateHelpers.ts
import { parseDate } from '@internationalized/date'

export function useDateHelpers() {
  // Asegura que un string UTC tenga 'Z' al final para interpretación correcta
  function ensureUTCString(dateString: string): string {
    if (!dateString) return dateString;
    if (typeof dateString === 'string' && !dateString.endsWith('Z') && !dateString.includes('+')) {
      return dateString + 'Z';
    }
    return dateString;
  }

  // Formatea una fecha UTC a formato local dd/mm/yy, hh:mm
  function formatLocalDate(utcString: string): string {
    if (!utcString) return 'N/D';
    const date = new Date(ensureUTCString(utcString));
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = String(date.getFullYear()).slice(-2);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${day}/${month}/${year}, ${hours}:${minutes}`;
  }

  // Convierte fecha y hora local a string UTC ISO
  function localToUTC(dateInput: any, timeStr: string): string {
    const dateStr = dateInput?.toString ? dateInput.toString() : dateInput;
    const date = new Date(`${dateStr}T${timeStr}:00`);
    return date.toISOString();
  }

  // Convierte un UTC Date a string "YYYY-MM-DDTHH:mm:ss" (hora local, sin Z)
  function dateToLocalString(utcDate: Date): string {
    const year = utcDate.getFullYear();
    const month = String(utcDate.getMonth() + 1).padStart(2, '0');
    const day = String(utcDate.getDate()).padStart(2, '0');
    const hours = String(utcDate.getHours()).padStart(2, '0');
    const minutes = String(utcDate.getMinutes()).padStart(2, '0');
    const seconds = String(utcDate.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
  }

  // Convierte UTC string a objeto { date, time } para inputs
  function utcToLocalInput(utcString: string): { date: string, time: string } {
    const date = new Date(ensureUTCString(utcString));
    const dateStr = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Europe/Madrid'
    }).format(date);
    const timeStr = new Intl.DateTimeFormat('es-ES', {
      timeZone: 'Europe/Madrid',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }).format(date);
    return { date: dateStr, time: timeStr };
  }

  return {
    ensureUTCString,
    formatLocalDate,
    localToUTC,
    dateToLocalString,
    utcToLocalInput,
    parseDate
  };
}
