# Ordering a replacement board assembled at JLCPCB (from KiCad)

How to get the pick-and-place (CPL) file right when a replacement or add-on board for a SAM machine is drawn in
KiCad and assembled by JLCPCB. Worked example: Tron LE's ramp tube emitter, rev D (ESP32-C3, six AL8860 bucks),
checked 2026-10-20 (observed: EasyEDA's footprints compared pad by pad with the KiCad 9.0.9 library).

- **JLC places its own library part, which is the part's EasyEDA footprint at 0°.** So the CPL rotation is
  KiCad's rotation plus an offset per *LCSC part*, the angle that turns EasyEDA's footprint (counter-clockwise from
  the top) onto KiCad's. Get EasyEDA's footprint with `pip install easyeda2kicad` then
  `easyeda2kicad --footprint --lcsc_id=Cxxxx --output DIR/lib` and compare pad numbers and positions; do not trust
  a package-name table alone.
- **Package tables (KiBot's, JLCKicadTools') are wrong for some parts.** On the Tron board: `^SOT-23` (180) also
  matched `SOT-23-5`, whose EasyEDA footprint (pins along X, pin 1 bottom left) needs 270; and `^CP_Elec_` (180)
  would have fitted the C3339 electrolytic reversed, since its EasyEDA pad 1 is + on the left like KiCad's (0).
  Diodes (SOD-123, SMA): EasyEDA pad 1 is the cathode, like KiCad, 0. SOT-23 180, SOIC and MSOP 270 held.
- **Position is EasyEDA's origin.** For modules check where EasyEDA puts it: the ESP32-C3-MINI-1's origin is the
  pad-array centre, the same as KiCad's, so moving the CPL point to the body centre (antenna included) puts it
  2.7 mm off. Connectors can differ by a few tenths (JST XH SM4-TB side entry: 0.25-0.4 mm).
- **Hand-fit parts with LCSC footprints**: EasyEDA may number pads differently from the maker's datasheet (Cree
  XM-L Color: EasyEDA 1-4 anodes, the KiCad footprint drawn from Cree's numbering has cathodes 1-4; pad n = 9-n,
  same polarity). Compare polarity marks and die pairing, not numbers.
- easyeda2kicad's 3D models come from `modules.easyeda.com`, the footprints from `easyeda.com`: a cloud session's
  network policy must allow both.
