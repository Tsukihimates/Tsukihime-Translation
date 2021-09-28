#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2018 AboodXD
# Licensed under GNU GPLv3

################################################################
################################################################


def getComponentsFromPixel(format_, pixel, comp):
    if format_ == 'l8':
        comp[2] = pixel & 0xFF

    elif format_ == 'la8':
        comp[2] = pixel & 0xFF
        comp[3] = (pixel & 0xFF00) >> 8

    elif format_ == 'la4':
        comp[2] = (pixel & 0xF) * 17
        comp[3] = ((pixel & 0xF0) >> 4) * 17

    elif format_ == 'rgb565':
        comp[2] = int((pixel & 0x1F) / 0x1F * 0xFF)
        comp[3] = int(((pixel & 0x7E0) >> 5) / 0x3F * 0xFF)
        comp[4] = int(((pixel & 0xF800) >> 11) / 0x1F * 0xFF)

    elif format_ == 'bgr565':
        comp[2] = int(((pixel & 0xF800) >> 11) / 0x1F * 0xFF)
        comp[3] = int(((pixel & 0x7E0) >> 5) / 0x3F * 0xFF)
        comp[4] = int((pixel & 0x1F) / 0x1F * 0xFF)

    elif format_ == 'rgb5a1':
        comp[2] = int((pixel & 0x1F) / 0x1F * 0xFF)
        comp[3] = int(((pixel & 0x3E0) >> 5) / 0x1F * 0xFF)
        comp[4] = int(((pixel & 0x7c00) >> 10) / 0x1F * 0xFF)
        comp[5] = ((pixel & 0x8000) >> 15) * 0xFF

    elif format_ == 'bgr5a1':
        comp[2] = int(((pixel & 0x7c00) >> 10) / 0x1F * 0xFF)
        comp[3] = int(((pixel & 0x3E0) >> 5) / 0x1F * 0xFF)
        comp[4] = int((pixel & 0x1F) / 0x1F * 0xFF)
        comp[5] = ((pixel & 0x8000) >> 15) * 0xFF

    elif format_ == 'a1bgr5':
        comp[2] = ((pixel & 0x8000) >> 15) * 0xFF
        comp[3] = int(((pixel & 0x7c00) >> 10) / 0x1F * 0xFF)
        comp[4] = int(((pixel & 0x3E0) >> 5) / 0x1F * 0xFF)
        comp[5] = int((pixel & 0x1F) / 0x1F * 0xFF)

    elif format_ == 'rgba4':
        comp[2] = (pixel & 0xF) * 17
        comp[3] = ((pixel & 0xF0) >> 4) * 17
        comp[4] = ((pixel & 0xF00) >> 8) * 17
        comp[5] = ((pixel & 0xF000) >> 12) * 17

    elif format_ == 'abgr4':
        comp[2] = ((pixel & 0xF000) >> 12) * 17
        comp[3] = ((pixel & 0xF00) >> 8) * 17
        comp[4] = ((pixel & 0xF0) >> 4) * 17
        comp[5] = (pixel & 0xF) * 17

    elif format_ == 'rgb8':
        comp[2] = pixel & 0xFF
        comp[3] = (pixel & 0xFF00) >> 8
        comp[4] = (pixel & 0xFF0000) >> 16

    elif format_ == 'bgr10a2':
        comp[2] = int((pixel & 0x3FF) / 0x3FF * 0xFF)
        comp[3] = int(((pixel & 0xFFC00) >> 10) / 0x3FF * 0xFF)
        comp[4] = int(((pixel & 0x3FF00000) >> 20) / 0x3FF * 0xFF)
        comp[5] = int(((pixel & 0xC0000000) >> 30) / 0x3 * 0xFF)

    elif format_ == 'rgba8':
        comp[2] = pixel & 0xFF
        comp[3] = (pixel & 0xFF00) >> 8
        comp[4] = (pixel & 0xFF0000) >> 16
        comp[5] = (pixel & 0xFF000000) >> 24

    elif format_ == 'bgra8':
        comp[2] = (pixel & 0xFF0000) >> 16
        comp[3] = (pixel & 0xFF00) >> 8
        comp[4] = pixel & 0xFF
        comp[5] = (pixel & 0xFF000000) >> 24

    return comp

def torgba8(width, height, data, format_, bpp, compSel):
    size = width * height * 4
    assert len(data) >= width * height * bpp

    new_data = bytearray(size)
    comp = [0, 0xFF, 0, 0, 0, 0xFF]

    if bpp not in [1, 2, 4]:
        return new_data

    for y in range(height):
        for x in range(width):
            pos = (y * width + x) * bpp
            pos_ = (y * width + x) * 4

            pixel = 0
            for i in range(bpp):
                pixel |= data[pos + i] << (8 * i)

            comp = getComponentsFromPixel(format_, pixel, comp)

            new_data[pos_ + 3] = comp[compSel[3]]
            new_data[pos_ + 2] = comp[compSel[2]]
            new_data[pos_ + 1] = comp[compSel[1]]
            new_data[pos_ + 0] = comp[compSel[0]]

    return bytes(new_data)


def rgb8torgbx8(data):
    numPixels = len(data) // 3

    new_data = bytearray(numPixels * 4)

    for i in range(numPixels):
        new_data[4 * i + 0] = data[3 * i + 0]
        new_data[4 * i + 1] = data[3 * i + 1]
        new_data[4 * i + 2] = data[3 * i + 2]
        new_data[4 * i + 3] = 0xFF

    return bytes(new_data)
