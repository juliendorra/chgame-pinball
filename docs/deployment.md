# Static editor deployment

Target: https://juliendorra.com/chgame-pinball/

The public repository contains the whole Pinball project. Only the contents
of `Pinball/build/studio/` are deployed. Source, firmware and native diagnostic
executables stay out of the website.

## Hosting and approval status

Account `juliendo-pinball` has home **www/chgame-pinball** and FTP-only access;
SFTP and SSH shell access are disabled. The standard FTP workflow is prepared
on `codex/scoped-ftp-approval`, pending explicit approval to transmit its
password and public site files without encryption. No files have been uploaded.

The OVH server rejects explicit FTPS (`AUTH TLS`), including after username
routing, and implicit FTPS on port 990 is unavailable. Automatic approval
review rejected the plaintext FTP switch because it exposes credentials and
site contents in transit.

An approved SFTP trial authenticated with pinned server keys, but its
canonical parent path differed from the login root. The confinement check
stopped before any upload. SFTP was disabled again because the required jail
could not be verified. Files outside the root were not read. The encrypted
implementation and its tests remain in source for a host providing a verifiable
SFTP jail; the public main workflow currently fails closed at this check.

## Prepared FTP workflow

It uses `SamKirkland/FTP-Deploy-Action`, following the existing
[juliendorra/blob-keyboard-simulator workflow](https://github.com/juliendorra/blob-keyboard-simulator/blob/main/.github/workflows/main.yaml).
The dedicated account is used with `server-dir: ./`, its configured root,
without another nested `www/chgame-pinball` directory.

Actions secrets are `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`. Their storage
in GitHub is encrypted, but standard FTP does **not** encrypt network traffic.
The pre-upload check rejects the login if `CWD ..`, `/` or `/../..` can leave
its initial directory. It performs no file writes. The FTP action syncs only
the static build directory and does not enable dangerous clean-slate deletion.

After publishing, each publicly served artifact is downloaded over HTTPS and
compared against its SHA-256, including the WASM MIME type. Apache deliberately
does not serve `.htaccess`, so it is excluded from HTTP readback.

## Site-only trigger

Publishing runs only for pushes to **main** changing site inputs: editor,
shared game C++, boards, sprites, bundled SDK, save implementation, dependencies,
browser build/test tools and deployment scripts/config. Documentation,
screenshots, research, cartridge metadata and compiler-only tooling do not
trigger it. There are no PR, branch, tag, schedule or manual publish triggers.
`tools/check_site_paths.py` guards the path filters.

Every deployment runs native/WASM state and pixel parity, browser interaction
and FAT checks, sanitized physics regressions and repeated synthetic games on
Linux. `.htaccess` sets the WASM MIME type and mutable-file revalidation.
The website needs no backend. HTTPS permits browser Web Serial.

## Retained SFTP implementation

`tools/deploy_sftp.py` verifies local artifacts, requires root confinement,
stages uploads, reads their SHA-256 back, and uses per-file atomic renames with
HTML and manifest last. It preserves unrelated files. It never opens a shell,
uses an SSH agent, disables host verification or falls back to plaintext.

`tools/deploy_known_hosts` pins public keys observed from the OVH-manager
hostname `ftp.cluster102.hosting.ovh.net` on 2026-11-09:

- ED25519: `SHA256:ZNtF/bBITy9lmYHPcrvIIT3C/vn9pH17arkLohMlbfw`
- RSA: `SHA256:Okot90+t/XLsatXvElUScQHr3qZZNs/L2nzN919ymHw`

This is first-use key pinning, not independent provider attestation. Subsequent
changes fail closed; verify an OVH rotation before updating the keys. The
five local deployment tests cover scope escape, corrupt upload, local hash
mismatch, traversal paths and preservation of unrelated/live files.
