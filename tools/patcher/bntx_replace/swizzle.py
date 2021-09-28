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


def DIV_ROUND_UP(n, d):
    return (n + d - 1) // d


def round_up(x, y):
    return ((x - 1) | (y - 1)) + 1


def pow2_round_up(x):
    x -= 1
    x |= x >> 1
    x |= x >> 2
    x |= x >> 4
    x |= x >> 8
    x |= x >> 16

    return x + 1


def getBlockHeight(height):
    blockHeight = pow2_round_up(height // 8)
    if blockHeight > 16:
        blockHeight = 16

    return blockHeight


def _swizzle(width, height, blkWidth, blkHeight, roundPitch, bpp, tileMode, blockHeightLog2, data, toSwizzle):
    assert 0 <= blockHeightLog2 <= 5
    blockHeight = 1 << blockHeightLog2

    width = DIV_ROUND_UP(width, blkWidth)
    height = DIV_ROUND_UP(height, blkHeight)

    if tileMode == 1:
        pitch = width * bpp

        if roundPitch:
            pitch = round_up(pitch, 32)

        surfSize = pitch * height

    else:
        pitch = round_up(width * bpp, 64)
        surfSize = pitch * round_up(height, blockHeight * 8)

    result = bytearray(surfSize)

    for y in range(height):
        for x in range(width):
            if tileMode == 1:
                pos = y * pitch + x * bpp

            else:
                pos = getAddrBlockLinear(x, y, width, bpp, 0, blockHeight)

            pos_ = (y * width + x) * bpp

            if pos + bpp <= surfSize:
                if toSwizzle:
                    result[pos:pos + bpp] = data[pos_:pos_ + bpp]

                else:
                    result[pos_:pos_ + bpp] = data[pos:pos + bpp]

    return result


def deswizzle(width, height, blkWidth, blkHeight, roundPitch, bpp, tileMode, blockHeightLog2, data):
    return _swizzle(width, height, blkWidth, blkHeight, roundPitch, bpp, tileMode, blockHeightLog2, bytes(data), 0)


def swizzle(width, height, blkWidth, blkHeight, roundPitch, bpp, tileMode, blockHeightLog2, data):
    return _swizzle(width, height, blkWidth, blkHeight, roundPitch, bpp, tileMode, blockHeightLog2, bytes(data), 1)


def getAddrBlockLinear(x, y, image_width, bytes_per_pixel, base_address, blockHeight):
    """
    From the Tegra X1 TRM
    """
    image_width_in_gobs = DIV_ROUND_UP(image_width * bytes_per_pixel, 64)

    GOB_address = (base_address
                   + (y // (8 * blockHeight)) * 512 * blockHeight * image_width_in_gobs
                   + (x * bytes_per_pixel // 64) * 512 * blockHeight
                   + (y % (8 * blockHeight) // 8) * 512)

    x *= bytes_per_pixel

    Address = (GOB_address + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64
               + ((x % 32) // 16) * 32 + (y % 2) * 16 + (x % 16))

    return Address
