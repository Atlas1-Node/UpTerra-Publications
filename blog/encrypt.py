#!/usr/bin/env python3
"""
Encrypts a plaintext HTML blog post with AES-256-GCM + PBKDF2 and wraps it
in a branded UpTerra login page.

Usage:   UPTERRA_PASSPHRASE=<pw> python3 encrypt.py <slug>
Example: UPTERRA_PASSPHRASE=... python3 encrypt.py 25-trillion-gallons
         → reads  _src/25-trillion-gallons.html  (plaintext source)
         → writes 25-trillion-gallons.html       (gated wrapper)

The passphrase is read from the UPTERRA_PASSPHRASE environment variable so
the secret never enters the repo. Export it in your shell profile or set it
inline on the command invocation.
"""

import sys, os, base64
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PASSWORD = os.environ.get("UPTERRA_PASSPHRASE", "").encode()
if not PASSWORD:
    sys.exit("UPTERRA_PASSPHRASE env var not set. Export it before running encrypt.py.")

def encrypt_blog(slug: str) -> None:
    here = Path(__file__).parent
    src_path = here / "_src" / f"{slug}.html"
    out_path = here / f"{slug}.html"

    if not src_path.exists():
        sys.exit(f"Source not found: {src_path}")

    plaintext = src_path.read_text(encoding="utf-8")

    salt = os.urandom(16)
    iv   = os.urandom(12)
    kdf  = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key  = kdf.derive(PASSWORD)

    ciphertext = AESGCM(key).encrypt(iv, plaintext.encode("utf-8"), None)
    blob = base64.b64encode(salt + iv + ciphertext).decode("ascii")

    gated = WRAPPER_TEMPLATE.replace("__BLOB__", blob)
    out_path.write_text(gated, encoding="utf-8")

    print(f"Encrypted {len(plaintext):,} chars → {len(ciphertext):,} bytes")
    print(f"Wrote gated wrapper: {out_path}")


WRAPPER_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>UpTerra Publications</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
  :root {
    --forest: #2D6A4F;
    --forest-dark: #1B4332;
    --sage: #74C69D;
    --cream: #F8F4EE;
    --ink: #0f1e36;
    --muted: #6B6B5E;
    --accent: #5ccf3d;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; }
  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--cream);
    color: var(--ink);
    display: grid;
    place-items: center;
    min-height: 100vh;
    padding: 2rem;
  }
  .gate {
    width: 100%;
    max-width: 420px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.6rem;
  }
  .gate img.logo {
    width: 240px;
    height: auto;
    user-select: none;
    -webkit-user-drag: none;
  }
  .eyebrow {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.32em;
    color: var(--muted);
    text-transform: uppercase;
  }
  form {
    display: flex;
    flex-direction: column;
    gap: 0.9rem;
    width: 100%;
    max-width: 280px;
    margin-top: 0.4rem;
  }
  input[type="password"] {
    background: transparent;
    border: none;
    border-bottom: 1.5px solid rgba(15, 30, 54, 0.18);
    color: var(--ink);
    font-family: inherit;
    font-size: 1rem;
    letter-spacing: 0.08em;
    text-align: center;
    padding: 0.6rem 0.2rem;
    outline: none;
    transition: border-color 0.25s ease;
  }
  input[type="password"]::placeholder { color: rgba(15, 30, 54, 0.35); }
  input[type="password"]:focus { border-bottom-color: var(--forest); }
  button {
    background: var(--forest);
    color: var(--cream);
    border: none;
    font-family: inherit;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    padding: 0.85rem 1.6rem;
    cursor: pointer;
    border-radius: 2px;
    transition: background 0.25s ease, transform 0.15s ease;
  }
  button:hover { background: var(--forest-dark); }
  button:active { transform: translateY(1px); }
  .error {
    font-size: 0.82rem;
    color: #b44a3a;
    min-height: 1.2rem;
    letter-spacing: 0.04em;
  }
  .footer {
    position: fixed;
    bottom: 1.2rem;
    left: 0; right: 0;
    text-align: center;
    font-size: 0.68rem;
    letter-spacing: 0.28em;
    color: rgba(15, 30, 54, 0.4);
    text-transform: uppercase;
  }
  @keyframes shake {
    0%,100% { transform: translateX(0); }
    20%,60% { transform: translateX(-6px); }
    40%,80% { transform: translateX(6px); }
  }
  .shake { animation: shake 0.45s ease; }
</style>
</head>
<body>
  <main class="gate">
    <img class="logo" src="../assets/upterra-logo.jpg" alt="UpTerra"/>
    <div class="eyebrow">Publications</div>
    <form id="gate-form" autocomplete="off">
      <input type="password" id="pw" placeholder="enter passphrase" autocomplete="off" spellcheck="false"/>
      <button type="submit">Enter</button>
      <div id="err" class="error" aria-live="polite"></div>
    </form>
  </main>
  <div class="footer">UpTerra &middot; Secured Content</div>

<script id="ct" type="application/octet-stream">__BLOB__</script>
<script>
(function(){
  'use strict';
  const BLOB = document.getElementById('ct').textContent.trim();

  async function decrypt(password) {
    const raw  = Uint8Array.from(atob(BLOB), c => c.charCodeAt(0));
    const salt = raw.slice(0, 16);
    const iv   = raw.slice(16, 28);
    const ct   = raw.slice(28);
    const enc  = new TextEncoder();
    try {
      const km = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
      const key = await crypto.subtle.deriveKey(
        { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
        km, { name: 'AES-GCM', length: 256 }, false, ['decrypt']
      );
      const plain = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, ct);
      return new TextDecoder().decode(plain);
    } catch (e) { return null; }
  }

  const form = document.getElementById('gate-form');
  const pw   = document.getElementById('pw');
  const err  = document.getElementById('err');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    err.textContent = '';
    const html = await decrypt(pw.value);
    if (html) {
      document.open();
      document.write(html);
      document.close();
    } else {
      pw.value = '';
      pw.classList.remove('shake');
      void pw.offsetWidth;
      pw.classList.add('shake');
      err.textContent = 'Incorrect passphrase.';
      pw.focus();
    }
  });

  pw.focus();
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 encrypt.py <slug>")
    encrypt_blog(sys.argv[1])
