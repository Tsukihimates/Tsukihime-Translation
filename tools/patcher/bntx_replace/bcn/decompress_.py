#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# BC3 Compressor/Decompressor
# Version 0.1
# Copyright © 2018 MasterVermilli0n / AboodXD

# decompress_.py
# A BC3/DXT5 decompressor in Python based on libtxc_dxtn.

################################################################
################################################################


def ToSigned8(v):
    if v > 255:
        return -1

    elif v < 0:
        return 0

    elif v > 127:
        return v - 256

    return v


def ToUnsigned8(v):
    if v > 127:
        return 127

    elif v < -128:
        return 128

    elif v < 0:
        return v + 256

    return v


def EXP5TO8R(packedcol):
    return (((packedcol) >> 8) & 0xf8) | (((packedcol) >> 13) & 0x07)


def EXP6TO8G(packedcol):
    return (((packedcol) >> 3) & 0xfc) | (((packedcol) >>  9) & 0x03)


def EXP5TO8B(packedcol):
    return (((packedcol) << 3) & 0xf8) | (((packedcol) >>  2) & 0x07)


def EXP4TO8(col):
    return col | col << 4


def dxt135_decode_imageblock(pixdata, img_block_src, i, j, dxt_type):
    color0 = pixdata[img_block_src] | (pixdata[img_block_src + 1] << 8)
    color1 = pixdata[img_block_src + 2] | (pixdata[img_block_src + 3] << 8)
    bits = (pixdata[img_block_src + 4] | (pixdata[img_block_src + 5] << 8) |
            (pixdata[img_block_src + 6] << 16) | (pixdata[img_block_src + 7] << 24))

    bit_pos = 2 * (j * 4 + i)
    code = (bits >> bit_pos) & 3

    ACOMP = 255
    if code == 0:
        RCOMP = EXP5TO8R(color0)
        GCOMP = EXP6TO8G(color0)
        BCOMP = EXP5TO8B(color0)

    elif code == 1:
        RCOMP = EXP5TO8R(color1)
        GCOMP = EXP6TO8G(color1)
        BCOMP = EXP5TO8B(color1)

    elif code == 2:
        if color0 > color1:
            RCOMP = ((EXP5TO8R(color0) * 2 + EXP5TO8R(color1)) // 3)
            GCOMP = ((EXP6TO8G(color0) * 2 + EXP6TO8G(color1)) // 3)
            BCOMP = ((EXP5TO8B(color0) * 2 + EXP5TO8B(color1)) // 3)

        else:
            RCOMP = ((EXP5TO8R(color0) + EXP5TO8R(color1)) // 2)
            GCOMP = ((EXP6TO8G(color0) + EXP6TO8G(color1)) // 2)
            BCOMP = ((EXP5TO8B(color0) + EXP5TO8B(color1)) // 2)

    elif code == 3:
        if dxt_type > 1 or color0 > color1:
            RCOMP = ((EXP5TO8R(color0) + EXP5TO8R(color1) * 2) // 3)
            GCOMP = ((EXP6TO8G(color0) + EXP6TO8G(color1) * 2) // 3)
            BCOMP = ((EXP5TO8B(color0) + EXP5TO8B(color1) * 2) // 3)

        else:
            RCOMP = 0
            GCOMP = 0
            BCOMP = 0

            if dxt_type == 1:
                ACOMP = 0
 
    return ACOMP, RCOMP, GCOMP, BCOMP


def dxt5_decode_alphablock(pixdata, blksrc, i, j):
    alpha0 = pixdata[blksrc]
    alpha1 = pixdata[blksrc + 1]

    bits = (pixdata[blksrc] | (pixdata[blksrc + 1] << 8) |
            (pixdata[blksrc + 2] << 16) | (pixdata[blksrc + 3] << 24) |
            (pixdata[blksrc + 4] << 32) | (pixdata[blksrc + 5] << 40) |
            (pixdata[blksrc + 6] << 48) | (pixdata[blksrc + 7] << 56)) >> 16

    for y in range(4):
        for x in range(4):
            if (x, y) == (i, j):
                code = bits & 0x07
                break

            bits >>= 3

    if code == 0:
        ACOMP = alpha0

    elif code == 1:
        ACOMP = alpha1

    elif alpha0 > alpha1:
        ACOMP = (alpha0 * (8 - code) + (alpha1 * (code - 1))) // 7

    elif code < 6:
        ACOMP = (alpha0 * (6 - code) + (alpha1 * (code - 1))) // 5

    elif code == 6:
        ACOMP = 0

    else:
        ACOMP = 255

    return ACOMP


def dxt5_decode_alphablock_signed(pixdata, blksrc, i, j):
    alpha0 = pixdata[blksrc]
    alpha1 = pixdata[blksrc + 1]

    bits = (pixdata[blksrc] | (pixdata[blksrc + 1] << 8) |
            (pixdata[blksrc + 2] << 16) | (pixdata[blksrc + 3] << 24) |
            (pixdata[blksrc + 4] << 32) | (pixdata[blksrc + 5] << 40) |
            (pixdata[blksrc + 6] << 48) | (pixdata[blksrc + 7] << 56)) >> 16

    for y in range(4):
        for x in range(4):
            if (x, y) == (i, j):
                code = bits & 0x07
                break

            bits >>= 3

    if code == 0:
        ACOMP = alpha0

    elif code == 1:
        ACOMP = alpha1

    elif ToSigned8(alpha0) > ToSigned8(alpha1):
        ACOMP = ToUnsigned8((ToSigned8(alpha0) * (8 - code) + (ToSigned8(alpha1) * (code - 1))) // 7)

    elif code < 6:
        ACOMP = ToUnsigned8((ToSigned8(alpha0) * (6 - code) + (ToSigned8(alpha1) * (code - 1))) // 5)

    elif code == 6:
        ACOMP = 0x80

    else:
        ACOMP = 0x7f

    return ACOMP


def fetch_2d_texel_rgba_dxt1(srcRowStride, pixdata, i, j):
    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 8
    ACOMP, RCOMP, GCOMP, BCOMP = dxt135_decode_imageblock(pixdata, blksrc, i & 3, j & 3, 1)
 
    return RCOMP, GCOMP, BCOMP, ACOMP


def fetch_2d_texel_rgba_dxt3(srcRowStride, pixdata, i, j):
    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 16
    ACOMP, RCOMP, GCOMP, BCOMP = dxt135_decode_imageblock(pixdata, blksrc + 8, i & 3, j & 3, 2)

    anibble = (pixdata[blksrc + ((j & 3) * 4 + (i & 3)) // 2] >> (4 * (i & 1))) & 0xf
    ACOMP = EXP4TO8(anibble)
 
    return RCOMP, GCOMP, BCOMP, ACOMP


def fetch_2d_texel_rgba_dxt5(srcRowStride, pixdata, i, j):
    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 16

    ACOMP = dxt5_decode_alphablock(pixdata, blksrc, i & 3, j & 3)
    _, RCOMP, GCOMP, BCOMP = dxt135_decode_imageblock(pixdata, blksrc + 8, i & 3, j & 3, 2)

    return RCOMP, GCOMP, BCOMP, ACOMP


def fetch_2d_texel_r_bc4(srcRowStride, pixdata, i, j):
    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 8
    RCOMP = dxt5_decode_alphablock(pixdata, blksrc, i & 3, j & 3)
 
    return RCOMP


def fetch_2d_texel_r_bc4_snorm(srcRowStride, pixdata, i, j):
    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 8
    RCOMP = dxt5_decode_alphablock_signed(pixdata, blksrc, i & 3, j & 3)
 
    return RCOMP


def fetch_2d_texel_rg_bc5(srcRowStride, pixdata, i, j):
    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 16

    RCOMP = dxt5_decode_alphablock(pixdata, blksrc, i & 3, j & 3)
    GCOMP = dxt5_decode_alphablock(pixdata, blksrc + 8, i & 3, j & 3)
 
    return RCOMP, GCOMP


def fetch_2d_texel_rg_bc5_snorm(srcRowStride, pixdata, i, j):
    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 16

    RCOMP = dxt5_decode_alphablock_signed(pixdata, blksrc, i & 3, j & 3)
    GCOMP = dxt5_decode_alphablock_signed(pixdata, blksrc + 8, i & 3, j & 3)
 
    return RCOMP, GCOMP


def decompressDXT1(data, width, height):
    output = bytearray(width * height * 4)
 
    for y in range(height):
        for x in range(width):
            R, G, B, A = fetch_2d_texel_rgba_dxt1(width, data, x, y)

            pos = (y * width + x) * 4

            output[pos + 0] = R
            output[pos + 1] = G
            output[pos + 2] = B
            output[pos + 3] = A
 
    return bytes(output)


def decompressDXT3(data, width, height):
    output = bytearray(width * height * 4)
 
    for y in range(height):
        for x in range(width):
            R, G, B, A = fetch_2d_texel_rgba_dxt3(width, data, x, y)

            pos = (y * width + x) * 4

            output[pos + 0] = R
            output[pos + 1] = G
            output[pos + 2] = B
            output[pos + 3] = A
 
    return bytes(output)


def decompressDXT5(data, width, height):
    output = bytearray(width * height * 4)
 
    for y in range(height):
        for x in range(width):
            R, G, B, A = fetch_2d_texel_rgba_dxt5(width, data, x, y)

            pos = (y * width + x) * 4

            output[pos + 0] = R
            output[pos + 1] = G
            output[pos + 2] = B
            output[pos + 3] = A
 
    return bytes(output)


def decompressBC4(data, width, height, SNORM):
    output = bytearray(width * height * 4)

    for y in range(height):
        for x in range(width):
            if SNORM:
                R = ToSigned8(fetch_2d_texel_r_bc4_snorm(width, data, x, y)) + 128

            else:
                R = fetch_2d_texel_r_bc4(width, data, x, y)

            pos = (y * width + x) * 4

            output[pos + 0] = R
            output[pos + 1] = R
            output[pos + 2] = R
            output[pos + 3] = 255
 
    return bytes(output)


def decompressBC5(data, width, height, SNORM):
    output = bytearray(width * height * 4)

    for y in range(height):
        for x in range(width):
            if SNORM:
                R, G = fetch_2d_texel_rg_bc5_snorm(width, data, x, y)

                R = ToSigned8(R) + 128
                G = ToSigned8(G) + 128

            else:
                R, G = fetch_2d_texel_rg_bc5(width, data, x, y)

            pos = (y * width + x) * 4

            output[pos + 0] = R
            output[pos + 1] = G
            output[pos + 2] = 0
            output[pos + 3] = 255
 
    return bytes(output)
