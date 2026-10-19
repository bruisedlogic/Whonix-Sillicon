#!/bin/bash
set -euo pipefail
umask 077

readonly TAG=18.2.1.9-developers-only
readonly COMMIT=3c25009d615ffd37a3544ddc32b9b507b0650bb6
readonly FINGERPRINT=916B8D99C38EAF5E8ADC7A2A8D66066A2EEACCDA

# Lima and some other builders use homes other than /home/<username>.
export HOMEVAR="$HOME"

[[ $(uname -s) == Linux && $(uname -m) == aarch64 && $EUID -ne 0 ]] || {
    echo 'Run as an ordinary user inside a disposable Debian 13 ARM64 VM.' >&2
    exit 1
}
. /etc/os-release
[[ $ID == debian && $VERSION_ID == 13 ]] || exit 1

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y git time curl approx \
    lsb-release fakeroot dpkg-dev fasttrack-archive-keyring safe-rm gnupg \
    sq sqop sequoia-git

keydir=$(mktemp -d)
trap 'rm -rf -- "$keydir"' EXIT
curl --fail --location --proto '=https' --tlsv1.2 \
    https://www.whonix.org/keys/derivative.asc -o "$keydir/derivative.asc"
actual=$(gpg --homedir "$keydir" --with-colons --import-options show-only \
    --import "$keydir/derivative.asc" | awk -F: '$1 == "fpr" {print $10; exit}')
[[ $actual == "$FINGERPRINT" ]] || { echo 'Signing fingerprint mismatch.' >&2; exit 1; }
gpg --homedir "$keydir" --import "$keydir/derivative.asc"

cd "$HOME"
if [[ ! -d derivative-maker ]]; then
    git clone --no-checkout --depth=1 --branch "$TAG" \
        https://github.com/Whonix/derivative-maker.git
fi
cd derivative-maker
[[ $(git rev-parse "refs/tags/$TAG^{commit}") == "$COMMIT" ]] || exit 1
GNUPGHOME="$keydir" git verify-tag "refs/tags/$TAG"
GNUPGHOME="$keydir" git verify-commit "$COMMIT"
git checkout --detach "$COMMIT"
[[ -z $(git status --porcelain) ]] || { echo 'Source checkout is modified.' >&2; exit 1; }
git submodule update --init --recursive --depth=1 --jobs=4
# A shallow checkout can omit the tag on a pinned submodule commit. Fetch that
# matching tag rather than relaxing upstream's signed-tag policy.
git submodule foreach --recursive '
    if test -z "$(git tag --points-at HEAD)"; then
        revision=$(git rev-parse HEAD)
        ref=$(git ls-remote --tags origin | awk -v revision="$revision" '\''
            $1 == revision {
                if (sub(/\^\{\}$/, "", $2)) {print $2; found=1; exit}
                fallback=$2
            }
            END {if (!found && fallback != "") print fallback}
        '\'')
        test -n "$ref" || { echo "No tag found for $displaypath at $revision" >&2; exit 1; }
        git fetch --depth=1 origin "$ref:$ref"
    fi
'

# Keep the upstream sanity and package-signature checks enabled.
# The upstream script may request further dependencies or sudo access.
for flavor in whonix-gateway-lxqt whonix-workstation-lxqt; do
    if [[ $flavor == whonix-gateway-lxqt ]]; then size=15G; else size=25G; fi
    # Upstream creates system configuration consumed by the unprivileged
    # approx service. Its directories/files need standard readable modes.
    (umask 022; ./derivative-maker --flavor "$flavor" --target utm --arch arm64 \
        --tb open --repo true --vmsize "$size")
done

echo 'Build completed. Images remain experimental until runtime release gates pass.'
