import { round as _round } from 'lodash';
import moment from 'moment';

export function abbreviate(value: string, maxlen: number): string {
  if (isNaN(maxlen)) maxlen=20;
  return value.substr(0, maxlen)+(value.length>maxlen ? '...' : '');
}

export function pluralize(value: number, word: string): string {
  return value === 1 ? word : `${word}s`;
}

const units = ['b', 'kb', 'Mb', 'Gb', 'Tb', 'Pb', 'Eb', 'Zb', 'Yb'];
export function prettyBytes(num: number): string {
  // jacked from: https://github.com/sindresorhus/pretty-bytes
  if (typeof num !== 'number' || isNaN(num)) {
    // throw new TypeError('Expected a number');
    return "0";
  }

  const neg = num < 0;

  if (neg) {
    num = -num;
  }

  if (num < 1) {
    return (neg ? '-' : '') + num + ' b';
  }

  const exponent = Math.min(Math.floor(Math.log(num) / Math.log(1000)), units.length - 1);
  const outNum = _round(num / Math.pow(1000, exponent), 1);
  const unit = units[exponent];

  return `${neg ? '-' : ''}${outNum} ${unit}`;
}

export function unPrettyBytes(pretty: string): number {
  const match = pretty.match(/^(-)?\s*([\d.]+)\s*((\w)[bB]?)?$/);
  const tunits = units.map(v => v.toLowerCase().substr(0,1));
  if (!match) {
    throw new Error('Invalid size string');
  }
  const neg = !!match[1];
  const num = parseFloat(match[2]);
  if (isNaN(num)) {
    throw new Error(`Cannot parse number from ${match[2]}`);
  }
  const exp = tunits.indexOf(match[3] === undefined ? 'b' : match[4].toLowerCase());
  if (exp == -1) {
    throw new Error(`Invalid exp ${match[3]}`);
  }
  return num * Math.pow(1000, exp) * (neg ? -1 : 1);
}

export function prettyDateTime(dt: Date | null): string {
  return dt ?
    moment(dt).format('YYYY-MM-DD HH:mm') : 
    '-';
}