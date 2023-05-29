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

import os.path

import dds
import globals

from structs import (
    BNTXHeader, TexContainer, BlockHeader, StringTable,
    TextureInfo, RelocTBL, readInt64, packInt64,
)

try:
    import pyximport; pyximport.install()
    import swizzle_cy as swizzle

except:
    import swizzle


DIV_ROUND_UP = swizzle.DIV_ROUND_UP
round_up = swizzle.round_up
pow2_round_up = swizzle.pow2_round_up


class File:
    def readFromFile(self, fname):
        with open(fname, "rb") as inf:
            inb = inf.read()

        return self.load(inb, 0)

    def load(self, data, pos):
        self.header = BNTXHeader()
        returnCode = self.header.load(data, pos)
        if returnCode:
            return returnCode

        pos += 32

        self.texContainer = TexContainer(self.header.endianness)
        returnCode = self.texContainer.load(data, pos)
        if returnCode:
            return returnCode

        self.target = self.texContainer.target.decode("utf-8")

        self.strTblHeader = BlockHeader(self.header.endianness)
        self.strTblHeader.load(data, self.header.firstBlkAddr)
        returnCode = self.strTblHeader.isValid(b'_STR')
        if returnCode:
            return returnCode

        self.strTbl = StringTable(self.header.endianness)
        self.strTbl.load(data, self.header.firstBlkAddr + 16)

        self.header.setNameIndex(self.strTbl)
        self.name = self.strTbl[self.header.nameIdx]

        pos = self.texContainer.dictAddr
        self.texNameDict = self.strTbl.TexNameDict(self.header.endianness, self.strTbl)
        self.texNameDict.load(data, pos)

        infoPtrsAddr = self.texContainer.infoPtrsAddr
        self.textures = []

        for i in range(self.texContainer.count):
            pos = readInt64(data, infoPtrsAddr + 8 * i, self.header.endianness)
            if data[pos:pos + 4] != b'BRTI':
                return 4

            texture = TextureInfo(self.header.endianness)
            texture.load(data, pos + 16)
            texture.setNameIndex(self.strTbl)
            texture.name = self.strTbl[texture.nameIdx]

            self.textures.append(texture)

        pos = self.header.relocAddr
        self.relocTblHeader = BlockHeader(self.header.endianness)
        self.relocTblHeader.load(data, pos)
        returnCode = self.relocTblHeader.isValid(b'_RLT')
        if returnCode:
            return returnCode

        self.relocTbl = RelocTBL(self.header.endianness)
        self.relocTbl.load(data, pos + 16, self.relocTblHeader.blockSize)

        return 0

    def rawData(self, texture):
        if (texture.format_ >> 8) in globals.blk_dims:
            blkWidth, blkHeight = globals.blk_dims[texture.format_ >> 8]

        else:
            blkWidth, blkHeight = 1, 1

        bpp = globals.bpps[texture.format_ >> 8]

        target = 1 if self.target == "NX  " else 0
        result_ = []

        linesPerBlockHeight = (1 << texture.blockHeightLog2) * 8
        blockHeightShift = 0

        for mipLevel, mipOffset in enumerate(texture.mipOffsets):
            width = max(1, texture.width >> mipLevel)
            height = max(1, texture.height >> mipLevel)

            size = DIV_ROUND_UP(width, blkWidth) * DIV_ROUND_UP(height, blkHeight) * bpp

            if pow2_round_up(DIV_ROUND_UP(height, blkHeight)) < linesPerBlockHeight:
                blockHeightShift += 1

            result = swizzle.deswizzle(
                width, height, blkWidth, blkHeight, target, bpp, texture.tileMode,
                max(0, texture.blockHeightLog2 - blockHeightShift), texture.data[mipOffset:],
            )

            result_.append(result[:size])

        return result_, blkWidth, blkHeight

    def extract(self, index, BFRESPath, exportAs, dontShowMsg=False):
        texture = self.textures[index]
        if texture.format_ in globals.formats and texture.dim == 2 and texture.arrayLength < 2 and texture.tileMode in globals.tileModes:
            if texture.format_ == 0x101:
                format_ = "la4"

            elif texture.format_ == 0x201:
                format_ = "l8"

            elif texture.format_ == 0x301:
                format_ = "rgba4"

            elif texture.format_ == 0x401:
                format_ = "abgr4"

            elif texture.format_ == 0x501:
                format_ = "rgb5a1"

            elif texture.format_ == 0x601:
                format_ = "a1bgr5"

            elif texture.format_ == 0x701:
                format_ = "rgb565"

            elif texture.format_ == 0x801:
                format_ = "bgr565"

            elif texture.format_ == 0x901:
                format_ = "la8"

            elif (texture.format_ >> 8) == 0xb:
                format_ = "rgba8"

            elif (texture.format_ >> 8) == 0xc:
                format_ = "bgra8"

            elif texture.format_ == 0xe01:
                format_ = "bgr10a2"

            elif (texture.format_ >> 8) == 0x1a:
                format_ = "BC1"

            elif (texture.format_ >> 8) == 0x1b:
                format_ = "BC2"

            elif (texture.format_ >> 8) == 0x1c:
                format_ = "BC3"

            elif texture.format_ == 0x1d01:
                format_ = "BC4U"

            elif texture.format_ == 0x1d02:
                format_ = "BC4S"

            elif texture.format_ == 0x1e01:
                format_ = "BC5U"

            elif texture.format_ == 0x1e02:
                format_ = "BC5S"

            elif texture.format_ == 0x1f05:
                format_ = "BC6H_SF16"

            elif texture.format_ == 0x1f0a:
                format_ = "BC6H_UF16"

            elif (texture.format_ >> 8) == 0x20:
                format_ = "BC7"

            elif texture.format_ == 0x3b01:
                format_ = "bgr5a1"

            result_, blkWidth, blkHeight = self.rawData(texture)

            name = texture.name.replace('\\', '_').replace('/', '_').replace(':', '_').replace('*', '_').replace(
                '?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')

            if (texture.format_ >> 8) in globals.ASTC_formats:
                file = os.path.join(BFRESPath, name + '.astc')

            else:
                file = os.path.join(BFRESPath, name + '.dds')

            if (texture.format_ >> 8) in globals.ASTC_formats:
                outBuffer = b''.join([
                    b'\x13\xAB\xA1\x5C', blkWidth.to_bytes(1, "little"),
                    blkHeight.to_bytes(1, "little"), b'\1',
                    texture.width.to_bytes(3, "little"),
                    texture.height.to_bytes(3, "little"), b'\1\0\0',
                    result_[0],
                ])

                with open(file, "wb+") as output:
                    output.write(outBuffer)

            else:
                hdr = dds.generateHeader(
                    texture.numMips, texture.width, texture.height, format_, texture.compSel,
                    len(result_[0]), (texture.format_ >> 8) in globals.BCn_formats,
                )

                with open(file, "wb+") as output:
                    output.write(b''.join([hdr, b''.join(result_)]))

        elif not dontShowMsg:
            msg = "Can't convert: " + texture.name

            if texture.format_ not in globals.formats:
                context = "Unsupported format."

            elif texture.tileMode not in globals.tileModes:
                context = "Unsupported tiling mode."

            elif texture.dim != 2:
                context = "Unsupported image storage dimension."

            else:
                context = "Unsupported array length."

            return False

    @staticmethod
    def getCurrentMipOffset_Size(width, height, blkWidth, blkHeight, bpp, currLevel):
        offset = 0

        for mipLevel in range(currLevel):
            width_ = DIV_ROUND_UP(max(1, width >> mipLevel), blkWidth)
            height_ = DIV_ROUND_UP(max(1, height >> mipLevel), blkHeight)

            offset += width_ * height_ * bpp

        width_ = DIV_ROUND_UP(max(1, width >> currLevel), blkWidth)
        height_ = DIV_ROUND_UP(max(1, height >> currLevel), blkHeight)

        size = width_ * height_ * bpp

        return offset, size


    def replace(self, texture, tileMode, SRGB, sparseBinding, sparseResidency, importMips, f):
        width, height, format_, fourcc, dataSize, compSel, numMips, data = dds.readDDS(f, SRGB)

        if 0 in [width, dataSize] and data == []:
            print("Unsupported DDS file!")
            return False

        if format_ not in globals.formats:
            print("Unsupported DDS format!")
            return False

        if not importMips:
            numMips = 1

        else:
            numMips = max(1, numMips + 1)

        if tileMode == 1:
            alignment = 1

        else:
            alignment = 512

        if (format_ >> 8) in globals.blk_dims:
            blkWidth, blkHeight = globals.blk_dims[format_ >> 8]

        else:
            blkWidth, blkHeight = 1, 1

        bpp = globals.bpps[format_ >> 8]

        if tileMode == 1:
            blockHeight = 1
            blockHeightLog2 = 0

            linesPerBlockHeight = 1

        else:
            blockHeight = swizzle.getBlockHeight(DIV_ROUND_UP(height, blkHeight))
            blockHeightLog2 = len(bin(blockHeight)[2:]) - 1

            linesPerBlockHeight = blockHeight * 8

        result = []
        surfSize = 0
        mipOffsets = []
        blockHeightShift = 0
        target = 1 if self.target == "NX  " else 0

        for mipLevel in range(numMips):
            offset, size = self.getCurrentMipOffset_Size(width, height, blkWidth, blkHeight, bpp, mipLevel)
            data_ = data[offset:offset + size]

            width_ = max(1, width >> mipLevel)
            height_ = max(1, height >> mipLevel)

            width__ = DIV_ROUND_UP(width_, blkWidth)
            height__ = DIV_ROUND_UP(height_, blkHeight)

            dataAlignBytes = b'\0' * (round_up(surfSize, alignment) - surfSize)
            surfSize += len(dataAlignBytes)
            mipOffsets.append(surfSize)

            if tileMode == 1:
                pitch = width__ * bpp

                if target == 1:
                    pitch = round_up(width__ * bpp, 32)

                surfSize += pitch * height__

            else:
                if pow2_round_up(height__) < linesPerBlockHeight:
                    blockHeightShift += 1

                pitch = round_up(width__ * bpp, 64)
                surfSize += pitch * round_up(height__, max(1, blockHeight >> blockHeightShift) * 8)

            result.append(bytearray(dataAlignBytes) + swizzle.swizzle(
                width_, height_, blkWidth, blkHeight, target, bpp, tileMode,
                max(0, blockHeightLog2 - blockHeightShift), data_,
            ))

        texture.readTexLayout = 1 if tileMode == 0 else 0
        texture.sparseBinding = sparseBinding
        texture.sparseResidency = sparseResidency
        texture.dim = 2
        texture.tileMode = tileMode
        texture.numMips = numMips
        texture.mipOffsets = mipOffsets
        texture.width = width
        texture.height = height
        texture.format_ = format_
        texture.accessFlags = 0x20
        texture.arrayLength = 1
        texture.blockHeightLog2 = blockHeightLog2
        texture.imageSize = surfSize
        texture.compSel = compSel
        texture.alignment = alignment
        texture.imgDim = 1
        texture.data = b''.join(result)

        return texture

    def save(self):
        self.relocTblHeader.blockSize = 2
        self.relocTbl.blocks = [self.relocTbl.Block(self.header.endianness), self.relocTbl.Block(self.header.endianness)]
        self.relocTbl.entries = []
        self.relocTbl.blocks[0].pos = 0
        self.relocTbl.blocks[0].relocEntryIdx = 0

        self.relocTbl.entries.append(self.relocTbl.Entry(self.header.endianness))
        self.relocTbl.entries[0].pos = 0x28
        self.relocTbl.entries[0].structs = [[0x28], [0x38]]
        self.relocTbl.entries[0].paddingCount = 1

        self.relocTbl.entries.append(self.relocTbl.Entry(self.header.endianness))
        self.relocTbl.entries[1].pos = 0x40
        self.relocTbl.entries[1].structs = [[0x40]]
        self.relocTbl.entries[1].paddingCount = 0

        pos = 0x198
        count = self.texContainer.count
        while count > 0:
            self.relocTbl.entries.append(self.relocTbl.Entry(self.header.endianness))
            self.relocTbl.entries[-1].pos = pos
            self.relocTbl.entries[-1].structs = [[pos + i * 8 for i in range(min(count, 0xFF))]]
            self.relocTbl.entries[-1].paddingCount = 0

            pos += min(count, 0xFF) * 8
            count -= 0xFF

        self.header.version = 0x40000
        self.header.alignmentShift = 0xC if self.texContainer.target == b'NX  ' else 3
        self.header.targetAddrSize = 0x40
        self.header.flag = 0

        self.strTbl.pos = 0x198 + 8 * self.texContainer.count + 16
        strTbl = self.strTbl.save()

        self.header.fileNameAddr = self.strTbl.getPosFromIndex(self.header.nameIdx) + 2
        self.header.firstBlkAddr = self.strTbl.pos - 16

        self.texNameDict.pos = self.strTbl.pos + len(strTbl)
        texNameDictAlignBytes = b'\0' * (round_up(self.texNameDict.pos, 8) - self.texNameDict.pos)
        self.texNameDict.pos += len(texNameDictAlignBytes)
        texNameDict = b''.join([texNameDictAlignBytes, self.texNameDict.save()])

        pos = self.texNameDict.pos + 16
        count = self.texNameDict.count + 1
        while count > 0:
            self.relocTbl.entries.append(self.relocTbl.Entry(self.header.endianness))
            self.relocTbl.entries[-1].pos = pos
            self.relocTbl.entries[-1].structs = [[pos + i * 8 for i in range(min(count, 0xFF))]]
            self.relocTbl.entries[-1].paddingCount = 0

            pos += min(count, 0xFF) * 8
            count -= 0xFF

        self.texContainer.dictAddr = self.texNameDict.pos
        self.texContainer.infoPtrsAddr = 0x198
        self.texContainer.memPoolAddr = 0x58
        self.texContainer.currMemPoolAddr = 0
        self.texContainer.baseMemPoolAddr = 0

        self.strTblHeader.blockSize = len(strTbl) + len(texNameDict) + 16
        self.strTblHeader.nextBlkAddr = self.strTblHeader.blockSize
        strTblHeader = self.strTblHeader.save()

        infoBlksPos = self.strTbl.pos - 16 + self.strTblHeader.nextBlkAddr
        infoBlks = bytearray()

        dataBlkHeader = BlockHeader(self.header.endianness)
        dataBlkHeader.magic = b'BRTD'
        dataBlkHeader.nextBlkAddr = 0

        dataBlkPos = infoBlksPos + 16
        for i in range(self.texContainer.count):
            dataBlkPos += 0x2A0 + 8 * self.textures[i].numMips

        self.relocTbl.blocks[0].size_ = dataBlkPos - 16

        dataAlignment = 1 << self.header.alignmentShift

        dataBlkAlignBytes = b'\0' * (round_up(dataBlkPos, dataAlignment) - dataBlkPos)
        dataBlkPos += len(dataBlkAlignBytes)
        self.texContainer.dataBlkAddr = dataBlkPos - 16
        dataBlk_ = bytearray()

        for i in range(self.texContainer.count):
            texture = self.textures[i]
            texture.pos = infoBlksPos + len(infoBlks) + 16
            texture.nameAddr = self.strTbl.getPosFromIndex(texture.nameIdx)
            texture.parentAddr = 0x20
            texture.ptrsAddr = texture.pos + 0x290
            texture.userDataAddr = 0
            texture.texPtr = texture.pos + 0x90
            texture.texViewPtr = texture.pos + 0x190
            texture.descSlotDataAddr = 0
            texture.userDictAddr = 0

            self.relocTbl.entries.append(self.relocTbl.Entry(self.header.endianness))
            self.relocTbl.entries[-1].pos = texture.pos + 0x50
            self.relocTbl.entries[-1].structs = [[texture.pos + 0x50, texture.pos + 0x58, texture.pos + 0x60]]
            self.relocTbl.entries[-1].paddingCount = 0

            self.relocTbl.entries.append(self.relocTbl.Entry(self.header.endianness))
            self.relocTbl.entries[-1].pos = texture.pos + 0x70
            self.relocTbl.entries[-1].structs = [[texture.pos + 0x70, texture.pos + 0x78]]
            self.relocTbl.entries[-1].paddingCount = 0

            infoBlkHeader = BlockHeader(self.header.endianness)
            infoBlkHeader.magic = b'BRTI'
            infoBlkHeader.blockSize = 0x2A0 + 8 * texture.numMips

            if i == self.texContainer.count - 1:
                infoBlkHeader.blockSize += len(dataBlkAlignBytes)

            infoBlkHeader.nextBlkAddr = infoBlkHeader.blockSize

            infoBlks += infoBlkHeader.save()
            infoBlks += texture.save()
            infoBlks += b'\0\0' * 0x100

            dataPos = dataBlkPos + len(dataBlk_)
            dataAlignBytes = b'\0' * (round_up(dataPos, texture.alignment) - dataPos)
            dataPos += len(dataAlignBytes)
            dataBlk_ += dataAlignBytes

            for offset in texture.mipOffsets:
                infoBlks += packInt64(dataPos + offset, self.header.endianness)

            dataBlk_ += texture.data

        self.header.relocAddr = dataBlkPos + len(dataBlk_)
        relocTblAlignBytes = b'\0' * (round_up(self.header.relocAddr, dataAlignment) - self.header.relocAddr)
        self.header.relocAddr += len(relocTblAlignBytes)
        dataBlk_ += relocTblAlignBytes

        dataBlkHeader.blockSize = len(dataBlk_) + 16
        dataBlk = b''.join([dataBlkAlignBytes, dataBlkHeader.save(), dataBlk_])

        self.relocTblHeader.magic = b'_RLT'
        self.relocTblHeader.nextBlkAddr = self.header.relocAddr
        self.relocTbl.blocks[0].relocEntryCount = len(self.relocTbl.entries)

        self.relocTbl.blocks[1].pos = self.texContainer.dataBlkAddr
        self.relocTbl.blocks[1].size_ = dataBlkHeader.blockSize
        self.relocTbl.blocks[1].relocEntryIdx = self.relocTbl.blocks[0].relocEntryCount

        self.relocTbl.entries.append(self.relocTbl.Entry(self.header.endianness))
        self.relocTbl.entries[-1].pos = 0x30
        self.relocTbl.entries[-1].structs = [[0x30]]
        self.relocTbl.entries[-1].paddingCount = 0

        for texture in self.textures:
            pos = texture.pos + 0x290
            count = texture.numMips
            while count > 0:
                self.relocTbl.entries.append(self.relocTbl.Entry(self.header.endianness))
                self.relocTbl.entries[-1].pos = pos
                self.relocTbl.entries[-1].structs = [[pos + i * 8 for i in range(min(count, 0xFF))]]
                self.relocTbl.entries[-1].paddingCount = 0

                pos += min(count, 0xFF) * 8
                count -= 0xFF

        self.relocTbl.blocks[1].relocEntryCount = len(self.relocTbl.entries) - self.relocTbl.blocks[1].relocEntryIdx

        relocTbl = b''.join([self.relocTblHeader.save(), self.relocTbl.save()])

        fileData = bytearray(self.texContainer.save())
        fileData += b'\0' * 0x140

        for i in range(self.texContainer.count):
            fileData += packInt64(self.textures[i].pos - 16, self.header.endianness)

        fileData += strTblHeader
        fileData += strTbl
        fileData += texNameDict
        fileData += infoBlks
        fileData += dataBlk
        fileData += relocTbl

        self.header.fileSize = len(fileData) + 32

        return b''.join([self.header.save(), fileData])
