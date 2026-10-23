#!/bin/sh
# wdt-pet -- reset the iPad back into iOS if Linux stops running.
#
# The S5L8940X watchdog sits in PMGR at 0x3f103020: +0x00 CUR_TIME (24 MHz,
# free-running, wraps every ~179 s), +0x04 BITE_TIME, +0x0c CTRL (bit 2 =
# reset enable).  CUR_TIME is left alone -- the kernel's tick reads it -- so
# instead of zeroing it, BITE_TIME is kept a minute ahead of it.  Near the
# wrap, where "a minute ahead" would itself wrap, reset is switched off until
# the counter comes round; that leaves about a third of each cycle unguarded.
# A hung kernel stops this loop, CUR_TIME reaches BITE_TIME, and the SoC
# resets into iOS.
AHEAD=$((60 * 24000000))
LIMIT=$((0xffffffff - AHEAD - 20 * 24000000))
while :; do
	cur=$((0x$(peek r 3f103020 1 | cut -d' ' -f2)))
	if [ "$cur" -lt "$LIMIT" ]; then
		peek w 3f103024 "$(printf %x $((cur + AHEAD)))" >/dev/null
		peek w 3f10302c 4 >/dev/null
	else
		peek w 3f10302c 0 >/dev/null
	fi
	sleep 5
done
