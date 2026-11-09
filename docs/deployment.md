# Static editor deployment

Target: https://juliendorra.com/chgame-pinball/

The public repository contains the whole Pinball project. Only the validated
contents of `Pinball/build/studio/` are uploaded. Source, firmware, native
diagnostics and unrelated files are not part of the website.

## Encrypted OVH connection

Deployment uses **SFTP on port 22**, with the dedicated `juliendo-pinball`
account rooted at **www/chgame-pinball** in OVH. SSH shell access is disabled.
This matches the FTP/SFTP configuration of the existing `juliendo-today`
account rooted at `www/today`.

`tools/deploy-target.json` pins the expected host, account and virtual SFTP
home. Actions secrets retain their original names: `FTP_SERVER`,
`FTP_USERNAME`, `FTP_PASSWORD`. The uploader rejects a different account or
host before authentication and never falls back to plaintext FTP.

OVH presents the isolated home as `/home/juliendo-pinball`. Its shared `/home`
container is readable metadata, rather than another site's storage. A strict
comparison requiring every parent to equal the login path incorrectly rejects
this namespace. The replacement guard verifies all of the following before
uploading:

- The canonical home matches the dedicated account, and is a real directory.
- Its parent is root-owned and non-writable by this account.
- The server root, primary account, Today I Die account and alternate web-root
  paths cannot be opened. These probes open and close directory handles
  without retrieving names or reading file contents.

After validation, every destination is relative to the verified home. Absolute
paths, traversal paths, local symlinks and remote symlink parents are rejected.
The account's backing OVH directory is verified in the signed-in control
panel; it remains `www/chgame-pinball`.

## Host keys and publication

`tools/deploy_known_hosts` pins keys observed from the OVH-manager hostname
`ftp.cluster102.hosting.ovh.net` on 2026-11-09:

- ED25519: `SHA256:ZNtF/bBITy9lmYHPcrvIIT3C/vn9pH17arkLohMlbfw`
- RSA: `SHA256:Okot90+t/XLsatXvElUScQHr3qZZNs/L2nzN919ymHw`

This is first-use key pinning, not independent provider attestation. Subsequent
key changes fail closed; verify an OVH rotation before changing this file.
The client disables SSH-agent and key discovery and never requests a shell.

Local artifact hashes are validated before any file write. All uploads receive
unique temporary names and complete SFTP SHA-256 readback before live files
are replaced. Engine files publish first, with HTML and manifest last. Only
manifest-listed files are written and unrelated server files are preserved.
Publication is atomic per file, not across all mutable JavaScript modules.

After upload, each publicly served artifact is downloaded over HTTPS and
checked against its SHA-256, including the WASM MIME type. Apache deliberately
does not serve `.htaccess`; that file is checked through SFTP readback.

## Site-only trigger and tests

Publishing runs only for pushes to **main** changing site inputs: editor,
shared game C++, boards, sprites, bundled SDK, save configuration and
implementation, dependencies, browser build/test tools and deployment code.
Documentation, screenshots, research, cartridge metadata and compiler-only
tooling do not trigger it. There are no PR, branch, tag, schedule or manual
publish triggers. `tools/check_site_paths.py` guards the filters; a real
documentation-only push was also verified to start no run.

Each deployment runs native/WASM state and pixel parity, browser interaction
and FAT checks, sanitized physics regressions and repeated synthetic games
on Linux. Eight deployment tests cover the permitted read-only container,
actual outside access, writable parents, benign parent metadata, wrong accounts,
corrupt uploads, local hash mismatches and traversal paths.

The site needs no backend. `.htaccess` sets the WASM MIME type and mutable-file
revalidation. HTTPS permits browser Web Serial. `tools/probe_sftp.py` provides
a read-only namespace check for diagnosis without publishing artifacts.
