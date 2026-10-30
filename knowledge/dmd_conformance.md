# Checking a recreation's DMD against PinMAME frame by frame

For any SAM game: does the recreation's classic 128x32 DMD draw what the ROM draws? Needed whenever something finds frames
by their dots (a Serum colourisation, a PuP trigger by picture), and a good regression measure otherwise. Worked example:
Tron Legacy LE 1.74 (`trn_174h`), Tron-Legacy-MPF `docs/dmd_conformance.md` and `scripts/conform/`.

## Method (observed, Tron, 2026-10-30)

1. **PinMAME dump.** libpinmame's `OnDisplayUpdated` callback, with `PinmameSetDmdMode(PINMAME_DMD_MODE_RAW)`, hands each
   frame of a SAM DMD as 128x32 bytes, `depth` 4: shades 0-15, the same levels as a recorded GIF (a GIF's grey / 17). Log
   `(emulated time, w, h, depth, bytes)` on every change, next to the rules trace of the same run (`tron_ref`; the Tron patch is
   `scripts/conform/tron_ref_dmddump.diff`). Same scenario script, same run: deterministic.
2. **The recreation's dump**: its classic DMD read back every rendered frame with the wall clock; the rules trace gets the wall
   clock too (the two processes share no clock).
3. **Align by the rules trace**: pair the `deff_start` events of both traces (same display effect id, in order, longest common
   subsequence) and compare the frames inside each pair's window with a small time tolerance (-0.2 / +0.6 s).
4. **The right metric is the colouriser's, not the dot count.** libserum identifies a frame by a CRC of the dots its per-frame
   comparison mask keeps (e.g. the status panel left out), sometimes by shape only, not by the whole picture. So measure
   "the Godot frame gets the same Serum frame id as PinMAME's", with the native decoder or libserum as the identifier: on Tron
   99.9 % of PinMAME's frames were known to the file, and the recreation matched 67 % (a whole-dot match was only 10 %).

## Gotchas

- libpinmame changes: the Tron `pinmame_arm_hook.patch` hunk on `libpinmame.cpp` (it appends at the end of the file) stopped
  applying to current PinMAME; apply the other files and append the hunk (Tron-Legacy-MPF `scripts/conform/build_tron_ref.sh`,
  PinMAME pinned at 540bbb1e).
- A ROM that differs from the PinMAME checksum (e.g. a version without music) still runs and gave the same effect trace.
- The ROM's animated transitions between text screens, the status panel and the boot version screen are where recreations
  differ first: a recreation that shows the final text over a static picture never produces the ROM's in-between frames.
