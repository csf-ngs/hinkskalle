import { prettyBytes, unPrettyBytes, prettyDateTime } from '@/util/pretty';

describe('prettyBytes', () => {
  it('makes bytes pretty', () => {
    const out = prettyBytes(1024);
    expect(out).toBe('1 kb');
  });
  it('rounds bytes', () => {
    const out = prettyBytes(12345);
    expect(out).toBe('12.1 kb');
    expect(prettyBytes(4567)).toBe('4.5 kb');
  });

});

describe('unPrettyBytes', () => {
  it('parses a simple number', () => {
    expect(unPrettyBytes('123')).toBe(123);
  });
  it('parses a negative number', () => {
    expect(unPrettyBytes('-123')).toBe(-123);
    expect(unPrettyBytes('- 123')).toBe(-123);
  });
  it('parses a simple suffix', () => {
    expect(unPrettyBytes('100 b')).toBe(100);
    expect(unPrettyBytes('100b')).toBe(100);
    expect(unPrettyBytes('100 kb')).toBe(102400);
    expect(unPrettyBytes('100 KB')).toBe(102400);
    expect(unPrettyBytes('100 k')).toBe(102400);
    expect(unPrettyBytes('100.2 kb')).toBe(102604.8);
    expect(unPrettyBytes('-100 kb')).toBe(-102400);
    expect(unPrettyBytes('100Gb')).toBe(107374182400);
    expect(unPrettyBytes('100g')).toBe(107374182400);
  });
});

describe('prettyDateTime', () => {
  it('formats a date object', () => {
    expect(prettyDateTime(new Date('1995-12-17T03:24:00'))).toBe('1995-12-17 03:24');
  });
  it('formats null', () => {
    expect(prettyDateTime(null)).toBe('-');
  })
});