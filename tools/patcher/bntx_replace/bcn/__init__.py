#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# DXT1/3/5 Decompressor
# Version 0.1
# Copyright © 2018 MasterVermilli0n / AboodXD

################################################################
################################################################

try:
    import pyximport
    pyximport.install()

    from . import decompress_cy as decompress_

except:
    from . import decompress_


def decompressDXT1(data, width, height):
    if not isinstance(data, bytes):
        try:
            data = bytes(data)

        except:
            print("Couldn't decompress data")
            return b''

    csize = ((width + 3) // 4) * ((height + 3) // 4) * 8
    if len(data) < csize:
        print("Compressed data is incomplete")
        return b''

    data = data[:csize]
    return decompress_.decompressDXT1(data, width, height)


def decompressDXT3(data, width, height):
    if not isinstance(data, bytes):
        try:
            data = bytes(data)

        except:
            print("Couldn't decompress data")
            return b''

    csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
    if len(data) < csize:
        print("Compressed data is incomplete")
        return b''

    data = data[:csize]
    return decompress_.decompressDXT3(data, width, height)


def decompressDXT5(data, width, height):
    if not isinstance(data, bytes):
        try:
            data = bytes(data)

        except:
            print("Couldn't decompress data")
            return b''

    csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
    if len(data) < csize:
        print("Compressed data is incomplete")
        return b''

    data = data[:csize]
    return decompress_.decompressDXT5(data, width, height)


def decompressBC4(data, width, height, SNORM=0):
    if not isinstance(data, bytes):
        try:
            data = bytes(data)

        except:
            print("Couldn't decompress data")
            return b''

    csize = ((width + 3) // 4) * ((height + 3) // 4) * 8
    if len(data) < csize:
        print("Compressed data is incomplete")
        return b''

    data = data[:csize]
    return decompress_.decompressBC4(data, width, height, SNORM)


def decompressBC5(data, width, height, SNORM=0):
    if not isinstance(data, bytes):
        try:
            data = bytes(data)

        except:
            print("Couldn't decompress data")
            return b''

    csize = ((width + 3) // 4) * ((height + 3) // 4) * 16
    if len(data) < csize:
        print("Compressed data is incomplete")
        return b''

    data = data[:csize]
    return decompress_.decompressBC5(data, width, height, SNORM)
