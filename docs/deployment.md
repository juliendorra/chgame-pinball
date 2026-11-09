# Static editor deployment

Production: https://juliendorra.com/chgame-pinball/

The public repository contains the whole Pinball project. Only the contents
of `Pinball/build/studio/` are uploaded; source, native diagnostics and firmware
are not deployed.

## OVH account and transport

Dedicated account: `juliendo-pinball`, home **www/chgame-pinball**, FTP and SFTP
enabled, SSH shell disabled. The uploader uses encrypted **SFTP only** on port
22 and rejects the login before uploading if parent traversal can leave its
configured root. It never requests a shell or executes commands on the host.

The existing repository workflows use `SamKirkland/FTP-Deploy-Action`. This
OVH cluster rejects `AUTH TLS`, so that action cannot provide encrypted FTPS
here. Plain FTP deployment was blocked by automatic approval review. The
replacement uses Paramiko with pinned server host keys and no plaintext fallback.

Repository Actions secrets retain their original names: `FTP_SERVER`,
`FTP_USERNAME`, `FTP_PASSWORD`. The FTP/SFTP hostname is the same one shown in
OVH's hosting control panel. Credentials belong in GitHub Secrets, never in
source or logs. The SFTP client disables SSH-agent/key discovery and accepts
only the configured account password and committed server keys.

`tools/deploy_known_hosts` records the public keys observed from
`ftp.cluster102.hosting.ovh.net` on 2026-11-09, bootstrapped from the local
connection to the hostname supplied by the signed-in OVH manager:

- ED25519: `SHA256:ZNtF/bBITy9lmYHPcrvIIT3C/vn9pH17arkLohMlbfw`
- RSA: `SHA256:Okot90+t/XLsatXvElUScQHr3qZZNs/L2nzN919ymHw`

This is first-use key pinning. Subsequent key changes fail closed; investigate
and verify an OVH rotation before updating this file. CI never auto-accepts a
new key and never disables host-key verification.

All local artifact hashes are checked before connection writes. Uploaded
files receive unique temporary names and complete SFTP SHA-256 readback before
any live file is replaced. Versioned engine files publish first; the entry
HTML and build manifest publish last. Only manifest-listed files are written;
unrelated server files are preserved. This is per-file atomic publication,
not a transaction across all mutable JavaScript files.

## Trigger scope

Publishing runs only for pushes to **main** changing site inputs: editor,
shared game C++, boards, sprites, bundled SDK sources, save implementation,
Python dependencies, browser build/test tools or deployment scripts/config.
Documentation, screenshots, research, cartridge metadata and compiler-only
tooling do not trigger it. There are no PR, branch, tag, schedule or manual
publish triggers. The workflow path list is checked by `tools/check_site_paths.py`.

Every deployment runs native/WASM state and pixel parity, browser interaction
and FAT checks, sanitized physics regressions and repeated synthetic games on
a Linux runner. `.htaccess` sets the WASM MIME type and mutable-file cache
revalidation. The site needs no backend; HTTPS permits browser Web Serial.

After publishing, every publicly served artifact is downloaded over HTTPS
and checked against its SHA-256, including WASM MIME verification. Apache's
private `.htaccess` is verified through SFTP, not an HTTP download.
