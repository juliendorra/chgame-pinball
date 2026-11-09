# Static editor deployment

Production: https://juliendorra.com/chgame-pinball/

The public repository contains the entire Pinball project. Only the contents
of `Pinball/build/studio/` are uploaded. Source, diagnostics executables,
firmware and unrelated game folders are not deployed.

The `deploy-editor.yml` workflow follows the FTP action used in
[juliendorra/blob-keyboard-simulator](https://github.com/juliendorra/blob-keyboard-simulator/blob/main/.github/workflows/main.yaml).
It uses explicit FTPS with certificate validation and a dedicated OVH user.

## OVH access and secrets

Create an FTP-only user with home directory **www/chgame-pinball**. Do not grant
SSH access. OVH adds the hosting account prefix to its username. Its login root
must resolve to this directory; the action therefore uploads to `./`, not to a
second nested `www/chgame-pinball` path.

Set repository Actions secrets `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`.
Use the OVH FTP hostname matching the server's TLS certificate. Credentials
belong in GitHub Secrets, never in this repository or in deployment logs.
The workflow verifies TLS and rejects the login if parent traversal can leave
its configured root, before uploading any file.

## Trigger scope

Automatic publishing runs only for pushes to **main** changing site inputs:
editor HTML/JS/CSS, game C++/headers, boards, sprites, the bundled SDK sources,
SD-save implementation, Python dependencies and browser build/test tools.
The workflow file itself is also a deployment input. Documentation, screenshots,
research, cartridge metadata and compiler-only tooling do not trigger it.
No pull-request, branch, tag, schedule or manual-dispatch deployment is configured.
The path list is in the workflow and is checked by `tools/check_site_paths.py`.

The C++ inputs are essential: changing physics must rebuild the browser engine
from those same sources. Every deployment runs native/WASM state and pixel
parity, browser interaction tests, FAT write checks and synthetic gameplay
regressions before FTP. Builds use a Linux runner; no macOS runner is needed.

`.htaccess` sets the WASM MIME type and revalidation for mutable files. URLs
are relative so the editor runs from its subdirectory. Browser Web Serial
requires HTTPS (or localhost) and Chrome/Edge support. No backend is hosted.

After upload, the workflow compares the live build's source hash and downloads
every listed artifact for SHA-256 verification. It also checks the WASM MIME
type. A successful transfer alone is not treated as a successful deployment.
