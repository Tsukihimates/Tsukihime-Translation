#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# BNTX Editor
# Version 0.3
# Copyright © 2018 AboodXD

# This file is part of BNTX Editor.

# BNTX Editor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BNTX Editor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import struct

try:
    import pyximport; pyximport.install()
    import formConv_cy as formConv

except:
    import formConv

dx10_formats = ["BC4U", "BC4S", "BC5U", "BC5S", "BC6H_UF16", "BC6H_SF16", "BC7"]


def readDDS(f, SRGB):
    with open(f, "rb") as inf:
        inb = inf.read()

    if len(inb) < 0x80 or inb[:4] != b'DDS ':
        return 0, 0, 0, b'', 0, [], 0, []

    width = struct.unpack("<I", inb[16:20])[0]
    height = struct.unpack("<I", inb[12:16])[0]

    fourcc = inb[84:88]

    pflags = struct.unpack("<I", inb[80:84])[0]
    bpp = struct.unpack("<I", inb[88:92])[0] >> 3
    channel0 = struct.unpack("<I", inb[92:96])[0]
    channel1 = struct.unpack("<I", inb[96:100])[0]
    channel2 = struct.unpack("<I", inb[100:104])[0]
    channel3 = struct.unpack("<I", inb[104:108])[0]
    caps = struct.unpack("<I", inb[108:112])[0]

    if caps not in [0x1000, 0x401008]:
        return 0, 0, 0, b'', 0, [], 0, []

    abgr8_masks = {0xff: 2, 0xff00: 3, 0xff0000: 4, 0xff000000: 5, 0: 1}
    bgr8_masks = {0xff: 2, 0xff00: 3, 0xff0000: 4, 0: 1}
    a2rgb10_masks = {0x3ff00000: 2, 0xffc00: 3, 0x3ff: 4, 0xc0000000: 5, 0: 1}
    bgr565_masks = {0x1f: 2, 0x7e0: 3, 0xf800: 4, 0: 1}
    a1bgr5_masks = {0x1f: 2, 0x3e0: 3, 0x7c00: 4, 0x8000: 5, 0: 1}
    abgr4_masks = {0xf: 2, 0xf0: 3, 0xf00: 4, 0xf000: 5, 0: 1}
    l8_masks = {0xff: 2, 0: 1}
    a8l8_masks = {0xff: 2, 0xff00: 3, 0: 1}
    a4l4_masks = {0xf: 2, 0xf0: 3, 0: 1}

    compressed = False
    luminance = False
    rgb = False
    has_alpha = False

    if pflags == 4:
        compressed = True

    elif pflags == 0x20000 or pflags == 2:
        luminance = True

    elif pflags == 0x20001:
        luminance = True
        has_alpha = True

    elif pflags == 0x40:
        rgb = True

    elif pflags == 0x41:
        rgb = True
        has_alpha = True

    else:
        return 0, 0, 0, b'', 0, [], 0, []

    format_ = 0
    compSel = [2, 3, 4, 5]

    if fourcc == b'DX10':
        if not compressed:
            return 0, 0, 0, b'', 0, [], 0, []

        headSize = 0x94

    else:
        headSize = 0x80

    if compressed:
        if fourcc == b'DXT1':
            format_ = 0x1a06 if SRGB else 0x1a01
            bpp = 8

        elif fourcc == b'DXT3':
            format_ = 0x1b06 if SRGB else 0x1b01
            bpp = 16

        elif fourcc == b'DXT5':
            format_ = 0x1c06 if SRGB else 0x1c01
            bpp = 16

        elif fourcc in [b'BC4U', b'ATI1']:
            format_ = 0x1d01
            bpp = 8

            compSel = [2, 2, 2, 1]

        elif fourcc == b'BC4S':
            format_ = 0x1d02
            bpp = 8

            compSel = [2, 2, 2, 1]

        elif fourcc in [b'BC5U', b'ATI2']:
            format_ = 0x1e01
            bpp = 16

            compSel = [2, 3, 0, 1]

        elif fourcc == b'BC5S':
            format_ = 0x1e02
            bpp = 16
            compSel = [2, 3, 0, 1]

        elif fourcc == b'DX10':
            if inb[128:148] == b"\x50\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00":
                format_ = 0x1d01
                bpp = 8

                compSel = [2, 2, 2, 1]

            elif inb[128:148] == b"\x51\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00":
                format_ = 0x1d02
                bpp = 8

                compSel = [2, 2, 2, 1]

            elif inb[128:148] == b"\x53\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00":
                format_ = 0x1e01
                bpp = 16

                compSel = [2, 3, 0, 1]

            elif inb[128:148] == b"\x54\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00":
                format_ = 0x1e02
                bpp = 16

                compSel = [2, 3, 0, 1]

            elif inb[128:148] == b"\x5F\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00":
                format_ = 0x1f0a
                bpp = 16

            elif inb[128:148] == b"\x60\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00":
                format_ = 0x1f05
                bpp = 16

            elif inb[128:148] == b"\x62\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00":
                format_ = 0x2006 if SRGB else 0x2001
                bpp = 16

            elif inb[128:148] == b"\x63\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00":
                format_ = 0x2006
                bpp = 16

        size = ((width + 3) >> 2) * ((height + 3) >> 2) * bpp

    else:
        if luminance:
            if has_alpha:
                if channel0 in a8l8_masks and channel1 in a8l8_masks and channel2 in a8l8_masks and channel3 in a8l8_masks and bpp == 2:
                    format_ = 0x901

                    compSel = [a8l8_masks[channel0], a8l8_masks[channel1], a8l8_masks[channel2], a8l8_masks[channel3]]

                elif channel0 in a4l4_masks and channel1 in a4l4_masks and channel2 in a4l4_masks and channel3 in a4l4_masks and bpp == 1:
                    format_ = 0x101

                    compSel = [a4l4_masks[channel0], a4l4_masks[channel1], a4l4_masks[channel2], a4l4_masks[channel3]]

            else:
                if channel0 in l8_masks and channel1 in l8_masks and channel2 in l8_masks and channel3 in l8_masks and bpp == 1:
                    format_ = 0x201

                    compSel = [l8_masks[channel0], l8_masks[channel1], l8_masks[channel2], l8_masks[channel3]]

        elif rgb:
            if has_alpha:
                if bpp == 4:
                    if channel0 in abgr8_masks and channel1 in abgr8_masks and channel2 in abgr8_masks and channel3 in abgr8_masks:
                        format_ = 0xb06 if SRGB else 0xb01

                        compSel = [abgr8_masks[channel0], abgr8_masks[channel1], abgr8_masks[channel2],
                                   abgr8_masks[channel3]]

                    elif channel0 in a2rgb10_masks and channel1 in a2rgb10_masks and channel2 in a2rgb10_masks and channel3 in a2rgb10_masks:
                        format_ = 0xe01

                        compSel = [a2rgb10_masks[channel0], a2rgb10_masks[channel1], a2rgb10_masks[channel2],
                                   a2rgb10_masks[channel3]]

                elif bpp == 2:
                    if channel0 in a1bgr5_masks and channel1 in a1bgr5_masks and channel2 in a1bgr5_masks and channel3 in a1bgr5_masks:
                        format_ = 0x501

                        compSel = [a1bgr5_masks[channel0], a1bgr5_masks[channel1], a1bgr5_masks[channel2],
                                   a1bgr5_masks[channel3]]

                    elif channel0 in abgr4_masks and channel1 in abgr4_masks and channel2 in abgr4_masks and channel3 in abgr4_masks:
                        format_ = 0x301

                        compSel = [abgr4_masks[channel0], abgr4_masks[channel1], abgr4_masks[channel2],
                                   abgr4_masks[channel3]]

            else:
                if channel0 in bgr8_masks and channel1 in bgr8_masks and channel2 in bgr8_masks and channel3 == 0 and bpp == 3:  # Kinda not looking good if you ask me
                    format_ = 0xb06 if SRGB else 0xb01

                    compSel = [bgr8_masks[channel0], bgr8_masks[channel1], bgr8_masks[channel2], 1]

                if channel0 in bgr565_masks and channel1 in bgr565_masks and channel2 in bgr565_masks and channel3 in bgr565_masks and bpp == 2:
                    format_ = 0x701

                    compSel = [bgr565_masks[channel0], bgr565_masks[channel1], bgr565_masks[channel2],
                               bgr565_masks[channel3]]

        size = width * height * bpp

    if caps == 0x401008:
        numMips = struct.unpack("<I", inb[28:32])[0] - 1
        mipSize = get_mipSize(width, height, bpp, numMips, compressed)

    else:
        numMips = 0
        mipSize = 0

    if len(inb) < headSize + size + mipSize:
        return 0, 0, 0, b'', 0, [], 0, []

    if format_ == 0:
        return 0, 0, 0, b'', 0, [], 0, []

    data = bytearray(inb[headSize:headSize + size + mipSize])

    if format_ in [0xb01, 0xb06] and bpp == 3:
        data = formConv.rgb8torgbx8(data)
        bpp += 1
        size = width * height * bpp

    return width, height, format_, fourcc, size, compSel, numMips, bytes(data)


def get_mipSize(width, height, bpp, numMips, compressed):
    size = 0
    for i in range(numMips):
        level = i + 1
        if compressed:
            size += ((max(1, width >> level) + 3) >> 2) * ((max(1, height >> level) + 3) >> 2) * bpp

        else:
            size += max(1, width >> level) * max(1, height >> level) * bpp

    return size


def generateHeader(num_mipmaps, w, h, format_, compSel, size, compressed):
    hdr = bytearray(128)

    luminance = False
    RGB = False

    compSels = {}
    fmtbpp = 0
    fourcc = b''

    has_alpha = True

    if format_ == "rgba8":  # ABGR8
        RGB = True
        compSels = {2: 0x000000ff, 3: 0x0000ff00, 4: 0x00ff0000, 5: 0xff000000, 1: 0}
        fmtbpp = 4

    elif format_ == "bgra8":  # ARGB8
        RGB = True
        compSels = {2: 0x00ff0000, 3: 0x0000ff00, 4: 0x000000ff, 5: 0xff000000, 1: 0}
        fmtbpp = 4

    elif format_ == "bgr10a2":  # A2RGB10
        RGB = True
        compSels = {2: 0x3ff00000, 3: 0x000ffc00, 4: 0x000003ff, 5: 0xc0000000, 1: 0}
        fmtbpp = 4

    elif format_ == "rgb565":  # BGR565
        RGB = True
        compSels = {2: 0x0000001f, 3: 0x000007e0, 4: 0x0000f800, 5: 0, 1: 0}
        fmtbpp = 2
        has_alpha = False

    elif format_ == "bgr565":  # RGB565
        RGB = True
        compSels = {2: 0x0000f800, 3: 0x000007e0, 4: 0x0000001f, 5: 0, 1: 0}
        fmtbpp = 2
        has_alpha = False

    elif format_ == "rgb5a1":  # A1BGR5
        RGB = True
        compSels = {2: 0x0000001f, 3: 0x000003e0, 4: 0x00007c00, 5: 0x00008000, 1: 0}
        fmtbpp = 2

    elif format_ == "bgr5a1":  # A1RGB5
        RGB = True
        compSels = {2: 0x00007c00, 3: 0x000003e0, 4: 0x0000001f, 5: 0x00008000, 1: 0}
        fmtbpp = 2

    elif format_ == "a1bgr5":  # RGB5A1
        RGB = True
        compSels = {2: 0x00008000, 3: 0x00007c00, 4: 0x000003e0, 5: 0x0000001f, 1: 0}
        fmtbpp = 2

    elif format_ == "rgba4":  # ABGR4
        RGB = True
        compSels = {2: 0x0000000f, 3: 0x000000f0, 4: 0x00000f00, 5: 0x0000f000, 1: 0}
        fmtbpp = 2

    elif format_ == "abgr4":  # RGBA4
        RGB = True
        compSels = {2: 0x0000f000, 3: 0x00000f00, 4: 0x000000f0, 5: 0x0000000f, 1: 0}
        fmtbpp = 2

    elif format_ == "l8":  # L8
        luminance = True
        compSels = {2: 0x000000ff, 3: 0, 4: 0, 5: 0, 1: 0}
        fmtbpp = 1

        if compSel[3] != 2:
            has_alpha = False

    elif format_ == "la8":  # A8L8
        luminance = True
        compSels = {2: 0x000000ff, 3: 0x0000ff00, 4: 0, 5: 0, 1: 0}
        fmtbpp = 2

    elif format_ == "la4":  # A4L4
        luminance = True
        compSels = {2: 0x0000000f, 3: 0x000000f0, 4: 0, 5: 0, 1: 0}
        fmtbpp = 1

    flags = 0x00000001 | 0x00001000 | 0x00000004 | 0x00000002

    caps = 0x00001000

    if num_mipmaps == 0:
        num_mipmaps = 1

    elif num_mipmaps != 1:
        flags |= 0x00020000
        caps |= 0x00000008 | 0x00400000

    if not compressed:
        flags |= 0x00000008

        a = False

        if compSel[0] != 2 and compSel[1] != 2 and compSel[2] != 2 and compSel[3] == 2:  # ALPHA
            a = True
            pflags = 0x00000002

        elif luminance:  # LUMINANCE
            pflags = 0x00020000

        elif RGB:  # RGB
            pflags = 0x00000040

        else:  # Not possible...
            return b''

        if has_alpha and not a:
            pflags |= 0x00000001

        size = w * fmtbpp

    else:
        flags |= 0x00080000
        pflags = 0x00000004

        if format_ == "BC1":
            fourcc = b'DXT1'

        elif format_ == "BC2":
            fourcc = b'DXT3'

        elif format_ == "BC3":
            fourcc = b'DXT5'

        elif format_ in dx10_formats:
            fourcc = b'DX10'

    hdr[:4] = b'DDS '
    hdr[4:4 + 4] = 124 .to_bytes(4, 'little')
    hdr[8:8 + 4] = flags.to_bytes(4, 'little')
    hdr[12:12 + 4] = h.to_bytes(4, 'little')
    hdr[16:16 + 4] = w.to_bytes(4, 'little')
    hdr[20:20 + 4] = size.to_bytes(4, 'little')
    hdr[28:28 + 4] = num_mipmaps.to_bytes(4, 'little')
    hdr[76:76 + 4] = 32 .to_bytes(4, 'little')
    hdr[80:80 + 4] = pflags.to_bytes(4, 'little')

    if compressed:
        hdr[84:84 + 4] = fourcc

    else:
        hdr[88:88 + 4] = (fmtbpp << 3).to_bytes(4, 'little')

        if compSel[0] in compSels:
            hdr[92:92 + 4] = compSels[compSel[0]].to_bytes(4, 'little')

        else:
            hdr[92:92 + 4] = compSels[2].to_bytes(4, 'little')

        if compSel[1] in compSels:
            hdr[96:96 + 4] = compSels[compSel[1]].to_bytes(4, 'little')

        else:
            hdr[96:96 + 4] = compSels[3].to_bytes(4, 'little')

        if compSel[2] in compSels:
            hdr[100:100 + 4] = compSels[compSel[2]].to_bytes(4, 'little')

        else:
            hdr[100:100 + 4] = compSels[4].to_bytes(4, 'little')

        if compSel[3] in compSels:
            hdr[104:104 + 4] = compSels[compSel[3]].to_bytes(4, 'little')

        else:
            hdr[104:104 + 4] = compSels[5].to_bytes(4, 'little')

    hdr[108:108 + 4] = caps.to_bytes(4, 'little')

    if format_ == "BC4U":
        hdr += bytearray(b"\x50\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")

    elif format_ == "BC4S":
        hdr += bytearray(b"\x51\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")

    elif format_ == "BC5U":
        hdr += bytearray(b"\x53\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")

    elif format_ == "BC5S":
        hdr += bytearray(b"\x54\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")

    elif format_ == "BC6H_UF16":
        hdr += bytearray(b"\x5F\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")

    elif format_ == "BC6H_SF16":
        hdr += bytearray(b"\x60\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")

    elif format_ == "BC7":
        hdr += bytearray(b"\x62\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")

    return hdr
