# Source and license information

The VM images contain upstream software under many licenses. The repository's MIT license covers only its original integration scripts/documentation, not Debian, Whonix, Kicksecure or Tor Browser. Whonix compilation licensing includes AGPL-3.0 and additional terms; see the actual copyright notices. This project is independent and does not claim endorsement.

`Package-and-License-Inventories.tar.gz` contains the exact installed binary/source versions, application entries, package copyright notices and common license texts for each VM.

Corresponding source is available without charge:

- `Whonix-Corresponding-Integration-Source.tar.gz`: tracked upstream build/integration source, including every pinned submodule. SOURCE-REVISIONS.json identifies official source URLs and exact revisions. The main upstream revision is 3c25009d615ffd37a3544ddc32b9b507b0650bb6 (18.2.1.9-developers-only).
- `Whonix-Updated-Package-Sources.tar.gz`: source archives and Debian packaging for installed Whonix repository package versions, with SHA-256 values recorded from the repository source index.
- `src-firefox-tor-browser-153.5.0esr-16.0-1-build2.tar.xz` and `.asc`: official source for Tor Browser 16.0a14, verified against Tor Browser Developers primary key EF6E286DDA85EA2A4BA7DE684E2C6E8793298290. Original download: https://archive.torproject.org/tor-package-archive/torbrowser/16.0a14/ . The official browser binary archive was verified separately against that key before being cached unchanged.
- `DEBIAN-SOURCE-LOCATIONS.tsv`: version-specific public Debian Snapshot source-package locations for installed packages. These external archives provide original source, Debian patches and build metadata; the exact source version is in the package inventories. Select the version's source files, not merely a latest package. Debian packages can also be retrieved in a matching Debian builder using `apt-get source SOURCE=VERSION` when that version remains indexed; use Snapshot for older versions.
- The GitHub tag's source archives contain this project's build/setup/hardening scripts. Build inputs and signature checks are documented in scripts/build.sh, scripts/prepare_preview.sh and docs/build-provenance.json. Preparation expects fresh original raw images in ~/derivative-binary/18.2.1.9, qemu-nbd/zerofree, the official browser archive as ~/preview-release/browser.tar.xz, its signature and the pinned verified signing key in the preparation GNUPGHOME. Read the script before running in a disposable Debian ARM64 builder; it is not a macOS script. No reproducible bit-identical image claim is made.

The source assets and source locations are provided alongside the binaries. Retain access to corresponding source when redistributing, preserve applicable notices, and observe each component's license. Do not imply that an upstream signature authenticates these modified VM images. Release SHA-256 values are unsigned integrity checks.
