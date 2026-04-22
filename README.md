# UpTerra Publications

Host for UpTerra HTML pages — research topics, papers, blogs, and product ideas. Served via GitHub Pages.

## Structure

- `assets/` — shared assets (logo, etc.)
- `blog/` — gated blog posts
  - `blog/encrypt.py` — encrypts a plaintext source into a gated wrapper
  - `blog/<slug>.html` — published gated HTML (password-protected)
- `research/`, `papers/`, `products/` — TBD

## Blog posts

- [25 Trillion Gallons](blog/25-trillion-gallons.html) — on water reduction (gated)

## Password gate

Each blog post is encrypted client-side with AES-256-GCM + PBKDF2-HMAC-SHA256 (100k iterations). The Web Crypto API decrypts in the browser only after a correct passphrase; content never ships in plaintext. The passphrase is distributed out-of-band and is never stored in this repo.

## Updating a post

Plaintext sources live **locally only** at `blog/_src/<slug>.html` (gitignored; never committed). The encryption passphrase is read from the `UPTERRA_PASSPHRASE` environment variable so it stays out of the repo too. Set it in your shell before running the script.

```bash
export UPTERRA_PASSPHRASE='<your-passphrase>'   # keep this out of version control

$EDITOR blog/_src/<slug>.html
cd blog && python3 encrypt.py <slug>
git add <slug>.html && git commit -m "Update <slug>" && git push
```

If you clone this repo on a new machine and want to edit, you'll need to place the plaintext source at `blog/_src/<slug>.html` first (keep a personal backup) and set `UPTERRA_PASSPHRASE` in your shell.
