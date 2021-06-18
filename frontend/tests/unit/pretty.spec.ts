import { prettyBytes, unPrettyBytes } from '@/util/pretty';

describe('prettyBytes', () => {
  it('makes bytes pretty', () => {
    const out = prettyBytes(1000);
    expect(out).toBe('1 kb');
  });
  it('rounds bytes', () => {
    const out = prettyBytes(12345);
    expect(out).toBe('12.3 kb');
    expect(prettyBytes(4567)).toBe('4.6 kb');
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
    expect(unPrettyBytes('100 kb')).toBe(100000);
    expect(unPrettyBytes('100 KB')).toBe(100000);
    expect(unPrettyBytes('100 k')).toBe(100000);
    expect(unPrettyBytes('100.2 kb')).toBe(100200);
    expect(unPrettyBytes('-100 kb')).toBe(-100000);
    expect(unPrettyBytes('100Gb')).toBe(100000000000);
    expect(unPrettyBytes('100g')).toBe(100000000000);
  });
});