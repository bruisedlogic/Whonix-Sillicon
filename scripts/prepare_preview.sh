#!/bin/bash
set -euo pipefail
umask 077
base="$HOME/preview-release"
export GNUPGHOME="$base/gnupg"
status=$(gpg --batch --status-fd=1 --verify "$base/browser.tar.xz.asc" "$base/browser.tar.xz" 2>"$base/browser-signature.log")
[[ "$status" == *"[GNUPG:] VALIDSIG "*" EF6E286DDA85EA2A4BA7DE684E2C6E8793298290"* ]]
mkdir -p "$base/mnt" "$base/manifests"
mount="$base/mnt"
sudo modprobe nbd max_part=8
nbd_connected=false
cleanup_mounts() {
 for d in dev/pts dev proc sys; do
  if mountpoint -q "$mount/$d"; then sudo umount -R "$mount/$d"; fi
 done
 if mountpoint -q "$mount"; then sudo umount "$mount"; fi
 if [[ "$nbd_connected" == true ]]; then sudo qemu-nbd --disconnect /dev/nbd2; fi
}
trap cleanup_mounts EXIT
roles=${PREVIEW_ROLES:-"Gateway Workstation"}
for role in $roles; do
 [[ "$role" == Gateway || "$role" == Workstation ]] || exit 1
 lower=${role,,}
 raw="$base/$lower.raw"
 test ! -e "$raw"
 qemu-img convert -f raw -O raw "$HOME/derivative-binary/18.2.1.9/Whonix-$role-LXQt-18.2.1.9.arm64.raw" "$raw"
 sudo qemu-nbd --connect=/dev/nbd2 --format=raw "$raw"
 nbd_connected=true
 sudo udevadm settle
 sudo mount -t ext4 -o nodev,nosuid /dev/nbd2p2 "$mount"
 # A trusted build copy only. Never run these mounts or chroot operations on macOS.
 sudo mv "$mount/etc/resolv.conf" "$mount/etc/resolv.conf.preview-original"
 sudo cp /run/systemd/resolve/resolv.conf "$mount/etc/resolv.conf"
 sudo cp "$mount/etc/hosts" "$mount/etc/hosts.preview-original"
 for domain in deb.whonix.org deb.debian.org; do
  address=$(getent ahostsv4 "$domain" | head -1 | cut -d " " -f1)
  printf "%s %s\n" "$address" "$domain" | sudo tee -a "$mount/etc/hosts" >/dev/null
 done
 if sudo test -e "$mount/usr/sbin/policy-rc.d"; then sudo mv "$mount/usr/sbin/policy-rc.d" "$mount/usr/sbin/policy-rc.d.preview-original"; fi
 printf '#!/bin/sh\nexit 101\n' | sudo tee "$mount/usr/sbin/policy-rc.d" >/dev/null
 sudo chmod 755 "$mount/usr/sbin/policy-rc.d"
 sudo mount --bind /dev "$mount/dev"
 sudo mount -t devpts -o newinstance,ptmxmode=0666,mode=0620 devpts "$mount/dev/pts"
 sudo mount -t proc proc "$mount/proc"
 sudo mount --bind /sys "$mount/sys"
 sudo tee "$mount/tmp/preview.sources" >/dev/null <<'SOURCES'
Types: deb
URIs: https://deb.debian.org/debian
Suites: trixie trixie-updates trixie-backports
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: https://deb.debian.org/debian-security
Suites: trixie-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: https://deb.whonix.org
Suites: trixie
Components: main contrib non-free
Signed-By: /usr/share/keyrings/derivative.asc
SOURCES
 aptopts=(-o Dir::Etc::sourcelist=/tmp/preview.sources -o Dir::Etc::sourceparts=- -o Acquire::Retries=2 -o DPkg::Options::=--force-confold)
 sudo chroot "$mount" /usr/bin/apt-get.anondist-orig "${aptopts[@]}" update
 sudo chroot "$mount" /usr/bin/env DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get.anondist-orig "${aptopts[@]}" -y dist-upgrade
 sudo chroot "$mount" /usr/bin/env SKIP_SCRIPTS= bash /usr/libexec/initializer-dist/chroot-scripts-post.d/75_sources
 sudo chroot "$mount" /usr/bin/env SKIP_SCRIPTS= bash /usr/libexec/initializer-dist/chroot-scripts-post.d/80_cleanup
 sudo rm "$mount/usr/sbin/policy-rc.d" "$mount/etc/resolv.conf"
 if sudo test -e "$mount/usr/sbin/policy-rc.d.preview-original"; then sudo mv "$mount/usr/sbin/policy-rc.d.preview-original" "$mount/usr/sbin/policy-rc.d"; fi
 sudo mv "$mount/etc/resolv.conf.preview-original" "$mount/etc/resolv.conf"
 sudo mv "$mount/etc/hosts.preview-original" "$mount/etc/hosts"
 for d in dev proc sys; do sudo umount -R "$mount/$d"; done
 sudo install -d -m755 "$mount/etc/systemd/system/greetd.service.d" "$mount/usr/local/share/whonix-sillicon"
 sudo tee "$mount/etc/systemd/system/greetd.service.d/80-utm-software-renderer.conf" >/dev/null <<'RENDER'
[Service]
Environment=WLR_RENDERER=pixman
Environment=LIBGL_ALWAYS_SOFTWARE=1
Environment=QT_QUICK_BACKEND=software
RENDER
 sudo tee "$mount/etc/apt/sources.list.d/derivative.sources" >/dev/null <<'REPO'
Types: deb
URIs: tor+https://deb.whonix.org
Suites: trixie
Components: main contrib non-free
Enabled: yes
Signed-By: /usr/share/keyrings/derivative.asc
REPO
 if [[ "$role" == Workstation ]]; then
  sudo install -d -m755 "$mount/var/cache/tb-binary/.tb" "$mount/etc/torbrowser.d"
  sudo tar --no-same-owner -xJf "$base/browser.tar.xz" -C "$mount/var/cache/tb-binary/.tb"
  sudo chmod -R a+rX "$mount/var/cache/tb-binary/.tb"
  sudo mkdir -p "$mount/var/cache/tb-binary/.tb/tor-browser/Browser/Downloads"
  printf '# Explicit development-preview alpha channel. Not stable Tor Browser.\ntbb_download_alpha_version=true\n' | sudo tee "$mount/etc/torbrowser.d/80-whonix-sillicon-alpha.conf" >/dev/null
 fi
 if [[ "$role" == Workstation ]]; then sudo chmod 644 "$mount/etc/torbrowser.d/80-whonix-sillicon-alpha.conf"; fi
sudo chmod 644 "$mount/etc/systemd/system/greetd.service.d/80-utm-software-renderer.conf" "$mount/etc/apt/sources.list.d/derivative.sources"
printf 'UNOFFICIAL DEVELOPMENT PREVIEW. Unsupported Apple Silicon UTM integration. Alpha browser on Workstation. Not audited or suitable for sensitive activity. Guest reboot powers off; manually Start again.\nhttps://github.com/bruisedlogic/Whonix-Sillicon\n' | sudo tee "$mount/usr/local/share/whonix-sillicon/DEVELOPMENT-PREVIEW.txt" >/dev/null
 sudo chmod 644 "$mount/usr/local/share/whonix-sillicon/DEVELOPMENT-PREVIEW.txt"
 # No image has been booted. Reset build-time IDs and entropy before first use.
 sudo truncate -s0 "$mount/etc/machine-id"
 sudo rm -f "$mount/var/lib/dbus/machine-id"
 sudo ln -s /etc/machine-id "$mount/var/lib/dbus/machine-id"
 sudo rm -f "$mount/var/lib/systemd/random-seed" "$mount/var/lib/random-seed" "$mount/var/lib/urandom/random-seed"
 sudo find "$mount/etc/ssh" -maxdepth 1 -type f -name 'ssh_host_*' -delete
 sudo find "$mount/var/log" -type f -exec truncate -s0 {} +
 sudo rm -rf "$mount/tmp/"* "$mount/var/tmp/"*
 sudo chroot "$mount" /usr/bin/dpkg-query -W '-f=${binary:Package}\t${Version}\t${Architecture}\t${source:Package}\t${source:Version}\n' > "$base/manifests/$lower-packages.tsv"
 sudo cp "$mount/var/lib/anon-dist/gpl/damngpl_source" "$base/manifests/$lower-sources.txt"
 sudo cp "$mount/var/lib/anon-dist/gpl/damngpl_dget" "$base/manifests/$lower-source-package-versions.txt"
 (cd "$mount"; find usr/share/doc -name copyright -print0; find usr/share/common-licenses -type f -print0) > "$base/copyright-paths.list"
 sudo tar -czf "$base/manifests/$lower-copyrights.tar.gz" -C "$mount" --null -T "$base/copyright-paths.list"
 sudo test ! -s "$mount/etc/machine-id"
 sudo test -z "$(sudo find "$mount/home" -mindepth 1 -print -quit)"
 sudo test -z "$(sudo find "$mount/var/lib/tor" -mindepth 1 -print -quit 2>/dev/null || true)"
 sudo test ! -e "$mount/usr/local/lib/utm-validation.py"
 sudo find "$mount/usr/share/applications" -maxdepth 1 -name '*.desktop' -printf '%f\n' | sort > "$base/manifests/$lower-applications.txt"
 sudo umount "$mount"
 loop=/dev/nbd2p2
 fsck_rc=0; sudo e2fsck -fp "$loop" || fsck_rc=$?
 [[ "$fsck_rc" -le 1 ]] || { sudo qemu-nbd --disconnect /dev/nbd2; nbd_connected=false; exit "$fsck_rc"; }
 sudo zerofree "$loop"
 sudo qemu-nbd --disconnect /dev/nbd2; nbd_connected=false
 qemu-img convert -f raw -O qcow2 -o compat=1.1,lazy_refcounts=off "$raw" "$base/$lower.qcow2"
 qemu-img check "$base/$lower.qcow2"
 sha256sum "$base/$lower.qcow2"
done
