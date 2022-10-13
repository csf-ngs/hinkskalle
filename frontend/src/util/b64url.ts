

function unescape(str: string): string {
    return (str + '==='.slice((str.length + 3) % 4))
      .replace(/-/g, '+')
      .replace(/_/g, '/')
}
function escape(str: string): string {
    return str.replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '')
}

export function b64url_encode(ar: ArrayBuffer): string {
    return escape(btoa(String.fromCharCode(...new Uint8Array(ar))));
}

export function b64url_decode(str: string): Uint8Array {
    return Uint8Array.from(atob(unescape(str)), c => c.charCodeAt(0));
}