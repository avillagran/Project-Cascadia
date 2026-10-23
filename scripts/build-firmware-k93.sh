#!/usr/bin/env bash
#
# The K93AP (iPad 2 Wi-Fi, iPad2,1) boot chain, from a stock IPSW.
#
#   iBEC.patched.autogo.plain.dfu   signature patch plus the auto-go hook,
#                                   unencrypted: the kDFU route, which is the
#                                   only one this board has been tried on
#
# Only the iBEC.  kDFU sends Legacy iOS Kit's own pwned iBSS, and the firmware
# the P105 build also pulls out of the root filesystem (touch, Wi-Fi,
# Bluetooth, GPU) belongs to other parts on this board, so it is left out
# until each one is ported.
#
# Pinned to iOS 8.4.1 / 12H321 and iPad2,1, for the same reason as
# build-firmware.sh: scripts/firmware/patch-ibec-autogo-k93.py patches
# addresses inside this exact iBEC.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IPSW="${IPSW:-$ROOT/ipad21.ipsw}"
OUT="$ROOT/build/firmware"

# Public firmware keys for iPad2,1 / 12H321, from the community key database.
IBEC_IV="83220a369c9525f3febb3edd331c65fb"
IBEC_KEY="179027ef30b5008882d6dbd723ceb50c39cba40bb33ba620b71bcbc53ff2d424"

BOOTARGS="${BOOTARGS:-cs_enforcement_disable=1 debug=0x14}"

# MD5 of the decrypted stock iBEC, so a wrong IPSW or key fails here and not
# on the device.
KNOWN_IBEC_DEC_MD5="${KNOWN_IBEC_DEC_MD5:-}"

fail() { echo "error: $*" >&2; exit 1; }

[ -f "$IPSW" ] || fail "no IPSW at $IPSW -- pass IPSW=/path/to/iPad2,1_8.4.1_12H321_Restore.ipsw"

PATCHER="${PATCHER:-/usr/local/bin/iBoot32Patcher}"
command -v "$PATCHER" >/dev/null 2>&1 || [ -x "$PATCHER" ] \
    || fail "no iBoot32Patcher at $PATCHER -- rebuild the image: docker rmi cascadia-build"

mkdir -p "$OUT"

echo "==> iBEC: extract, decrypt, patch"
unzip -o -j "$IPSW" "Firmware/dfu/iBEC.k93.RELEASE.dfu" -d "$OUT" >/dev/null \
    || fail "iBEC not found in $IPSW -- is this an iPad2,1 8.4.1 IPSW?"
python3 "$ROOT/scripts/img3decrypt.py" \
    "$OUT/iBEC.k93.RELEASE.dfu" "$OUT/iBEC.dec" "$IBEC_IV" "$IBEC_KEY"
grep -aq "iBEC for k93" "$OUT/iBEC.dec" || fail "decrypted iBEC is not the K93 one"
if [ -n "$KNOWN_IBEC_DEC_MD5" ]; then
    [ "$(md5sum "$OUT/iBEC.dec" | cut -d' ' -f1)" = "$KNOWN_IBEC_DEC_MD5" ] \
        || fail "decrypted iBEC does not match $KNOWN_IBEC_DEC_MD5"
fi
"$PATCHER" "$OUT/iBEC.dec" "$OUT/iBEC.patched" -b "$BOOTARGS" >/dev/null

echo "==> iBEC: auto-go hook"
python3 "$ROOT/scripts/firmware/patch-ibec-autogo-k93.py" "$OUT/iBEC.patched" "$OUT/iBEC.autogo"

echo "==> iBEC: repack as img3 (plaintext -- the kDFU route)"
python3 "$ROOT/scripts/img3pack.py" \
    "$OUT/iBEC.k93.RELEASE.dfu" "$OUT/iBEC.autogo" \
    "$OUT/iBEC.patched.autogo.plain.dfu"

ls -l "$OUT/iBEC.patched.autogo.plain.dfu"
