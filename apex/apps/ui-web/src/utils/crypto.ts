/**
 * Cryptographic utilities for SHA256 hashing
 */

export async function sha256_digest(data: Uint8Array | string | ArrayBuffer): Promise<string> {
  let buffer: ArrayBuffer;
  if (typeof data === 'string') {
    buffer = new TextEncoder().encode(data).buffer;
  } else if (data instanceof Uint8Array) {
    buffer = data.buffer as ArrayBuffer;
  } else if (data instanceof SharedArrayBuffer) {
    throw new Error('SharedArrayBuffer not supported for hashing');
  } else {
    buffer = data as ArrayBuffer;
  }

  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}
