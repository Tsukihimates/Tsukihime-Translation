#!/usr/bin/env python3
import sys
import fontforge
import psMat

PUA_BASE = 0xE000
ITALIC_SKEW_RADS = 0.3


def pua_range(i):
    return (
        ("ranges", None),
        PUA_BASE + i * 128,
        PUA_BASE + (i + 1) * 128 - 1
    )


def apply_origin(font, function):
    for glyph in font.selection.byGlyphs:
        bb = glyph.boundingBox()
        cx = (bb[2] + bb[0]) / 2
        cy = (bb[3] + bb[1]) / 2
        translate_center = psMat.translate(-cx, -cy)
        glyph.transform(translate_center)
        function(glyph)
        translate_back = psMat.translate(cx, cy)
        glyph.transform(translate_back)


def main():
    # Open the source font
    font = fontforge.open(sys.argv[1])

    # Copy the base ASCII range
    font.selection.select(("ranges", None), 0, 127)
    font.copy()

    # Italic
    font.selection.select(*pua_range(0))
    font.paste()
    apply_origin(font, lambda g: g.transform(psMat.skew(ITALIC_SKEW_RADS)))

    # Reversed
    font.selection.select(*pua_range(1))
    font.paste()
    apply_origin(font, lambda g: g.transform(psMat.scale(-1, 1)))

    # Reversed _and_ italic
    font.selection.select(*pua_range(2))
    font.paste()
    apply_origin(
        font, lambda g: g.transform(psMat.compose(
                psMat.skew(ITALIC_SKEW_RADS), psMat.scale(-1, 1))))

    # Export
    font.generate(sys.argv[2])


if __name__ == '__main__':
    main()
