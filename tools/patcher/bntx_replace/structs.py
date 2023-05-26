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


class BNTXHeader:
    def _setFormat(self):
        self.format = self.endianness + '8sIH2BI2H2I'

    def load(self, data, pos):
        bom = data[pos + 12:pos + 14]
        if bom == b'\xFF\xFE':
            self.endianness = '<'

        elif bom == b'\xFE\xFF':
            self.endianness = '>'

        else:
            return 1

        self.bom = 0xFEFF
        self._setFormat()

        (self.magic,
         self.version,
         _,
         self.alignmentShift,
         self.targetAddrSize,
         self.fileNameAddr,
         self.flag,
         self.firstBlkAddr,
         self.relocAddr,
         self.fileSize) = struct.unpack_from(self.format, data, pos)

        if self.magic != b'BNTX\0\0\0\0':
            return 2

        return 0

    def setNameIndex(self, strTbl):
        self.nameIdx = strTbl.index(self.fileNameAddr - 2)

    def save(self):
        return struct.pack(
            self.format,
            self.magic,
            self.version,
            self.bom,
            self.alignmentShift,
            self.targetAddrSize,
            self.fileNameAddr,
            self.flag,
            self.firstBlkAddr,
            self.relocAddr,
            self.fileSize,
        )

    def __repr__(self):
        return (
            f"Format: {self.format}\n"
            f"Magic: {self.magic}\n"
            f"Version: {self.version}\n"
            f"Bom: {self.bom}\n"
            f"Alignment Shift: {self.alignmentShift}\n"
            f"TargetAddrSize: {self.fileNameAddr}\n"
            f"FileNameAddr: {self.fileNameAddr}\n"
            f"Flag: {self.flag}\n"
            f"FirstBlkAddr: {self.firstBlkAddr}\n"
            f"RelocAddr: {self.relocAddr}\n"
            f"FileSize: {self.fileSize}\n"
        )


class TexContainer:
    def __init__(self, endianness):
        self.format = endianness + '4sI5qI4x'

    def load(self, data, pos):
        (self.target,
         self.count,
         self.infoPtrsAddr,
         self.dataBlkAddr,
         self.dictAddr,
         self.memPoolAddr,
         self.currMemPoolAddr,
         self.baseMemPoolAddr) = struct.unpack_from(self.format, data, pos)

        if self.target not in [b'NX  ', b'Gen ']:
            return 3

        return 0

    def save(self):
        return struct.pack(
            self.format,
            self.target,
            self.count,
            self.infoPtrsAddr,
            self.dataBlkAddr,
            self.dictAddr,
            self.memPoolAddr,
            self.currMemPoolAddr,
            self.baseMemPoolAddr,
        )


class BlockHeader:
    def __init__(self, endianness):
        self.format = endianness + '4s2I4x'

    def load(self, data, pos):
        (self.magic,
         self.nextBlkAddr,
         self.blockSize) = struct.unpack_from(self.format, data, pos)

    def isValid(self, magic):
        if self.magic != magic:
            return 4

    def save(self):
        return struct.pack(
            self.format,
            self.magic,
            self.nextBlkAddr,
            self.blockSize,
        )


class StringTable:
    class TexNameDict:
        class Entry:
            def __init__(self, endianness):
                self.format = endianness + 'I2Hq'

            def load(self, data, pos, strTbl, isRoot):
                (self.referenceBit,
                 self.leftIdx,
                 self.rightIdx,
                 self.strTblEntryAddr) = struct.unpack_from(self.format, data, pos)

                if isRoot:
                    self.strIdx = -1

                else:
                    self.strIdx = strTbl.index(self.strTblEntryAddr)

            def save(self, strTbl):
                return struct.pack(
                    self.format,
                    self.referenceBit,
                    self.leftIdx,
                    self.rightIdx,
                    strTbl.getPosFromIndex(self.strIdx),
                )

        def __init__(self, endianness, strTbl):
            self.endianness = endianness
            self.format = endianness + '4sI'
            self.strTbl = strTbl

        def load(self, data, pos):
            self.pos = pos

            (self.magic,
             self.count) = struct.unpack_from(self.format, data, pos)

            entriesPos = pos + 8
            self.entries = []

            for i in range(self.count + 1):
                entryPos = entriesPos + 16 * i

                self.entries.append(self.Entry(self.endianness))
                self.entries[-1].load(data, entryPos, self.strTbl, not i)

        def save(self):
            outBuffer = bytearray(struct.pack(
                self.format,
                self.magic,
                self.count,
            ))

            for i in range(self.count + 1):
                outBuffer += self.entries[i].save(self.strTbl)

            return bytes(outBuffer)

    class Entry:
        def __init__(self, endianness):
            self.format = endianness + 'H'

        def load(self, data, pos):
            self.pos = pos
            self.size_ = struct.unpack_from(self.format, data, pos)[0]
            try:        
                self.string = data[pos + 2:pos + 2 + self.size_].decode('utf-8')
            except UnicodeDecodeError:
                self.string = data[pos + 2:pos + 2 + self.size_].decode('shift-jis')
                    
            

        def save(self):
            return b''.join([
                struct.pack(self.format, self.size_),
                self.string.encode('utf-8'), b'\0',
            ])

    def __init__(self, endianness):
        self.endianness = endianness
        self.format = endianness + 'I'
        self.entries = []

    def __getitem__(self, index):
        if not isinstance(index, int):
            raise TypeError("index must be an integer")

        return self.entries[index].string

    def __repr__(self):
        return str([entry.string for entry in self.entries])

    def load(self, data, pos):
        self.pos = pos
        self.count = struct.unpack_from(self.format, data, pos)[0]

        entriesPos = pos + 8
        self.entries = []

        for i in range(1, self.count + 1):
            self.entries.append(self.Entry(self.endianness))
            self.entries[-1].load(data, entriesPos)

            entriesPos += self.entries[-1].size_ + 3
            entriesPos = ((entriesPos - 1) | 1) + 1

    def getStringFromPos(self, pos):
        if isinstance(pos, int):
            for entry in self.entries:
                if pos == entry.pos:
                    return entry.string

        raise ValueError("String is not in the string table")

    def getPosFromString(self, string):
        if isinstance(string, str):
            for entry in self.entries:
                if string == entry.string:
                    return entry.pos

        raise ValueError("String is not in the string table")

    def getPosFromIndex(self, index):
        if index == -1:
            return self.pos + 4

        else:
            return self.entries[index].pos

    def index(self, item):
        if isinstance(item, str):
            for i, entry in enumerate(self.entries):
                if item == entry.string:
                    return i

        elif isinstance(item, int):
            for i, entry in enumerate(self.entries):
                if item == entry.pos:
                    return i

        raise ValueError("String is not in the string table")

    def save(self):
        outBuffer = bytearray(struct.pack(self.format, self.count))
        outBuffer += b'\0\0\0\0'

        entriesPos = self.pos + 8
        for i in range(self.count):
            self.entries[i].pos = entriesPos
            outBuffer += self.entries[i].save()

            entriesPos += self.entries[i].size_ + 3
            entryAlignBytes = b'\0' * ((((entriesPos - 1) | 1) + 1) - entriesPos)
            entriesPos += len(entryAlignBytes)
            outBuffer += entryAlignBytes

        return bytes(outBuffer)


class TextureInfo:
    def __init__(self, endianness):
        self.format = endianness + '2B4H2x2I3i3I20x3IB3x8q'

    def load(self, data, pos):
        self.pos = pos
        (self.flags,
         self.dim,
         self.tileMode,
         self.swizzle,
         self.numMips,
         self.numSamples,
         self.format_,
         self.accessFlags,
         self.width,
         self.height,
         self.depth,
         self.arrayLength,
         self.textureLayout,
         self.textureLayout2,
         self.imageSize,
         self.alignment,
         self._compSel,
         self.imgDim,
         self.nameAddr,
         self.parentAddr,
         self.ptrsAddr,
         self.userDataAddr,
         self.texPtr,
         self.texViewPtr,
         self.descSlotDataAddr,
         self.userDictAddr) = struct.unpack_from(self.format, data, pos)

        self.compSel = [(self._compSel >> (8 * i)) & 0xff for i in range(4)]
        self.readTexLayout = self.flags & 1
        self.sparseBinding = self.flags >> 1
        self.sparseResidency = self.flags >> 2
        self.blockHeightLog2 = self.textureLayout & 7

        firstMipOffset = readInt64(data, self.ptrsAddr, self.format[:1])
        self.mipOffsets = [0]

        for i in range(1, self.numMips):
            self.mipOffsets.append(readInt64(data, self.ptrsAddr + 8 * i, self.format[:1]) - firstMipOffset)

        self.data = data[firstMipOffset:firstMipOffset + self.imageSize]

    def __repr__(self):
        return (
            f"Flags: {self.flags}\n"
            f"Dim: {self.dim}\n"
            f"Tile Mode: {self.tileMode}\n"
            f"Swizzle: {self.swizzle}\n"
            f"Num mips: {self.numMips}\n"
            f"Num samples: {self.numSamples}\n"
            f"Format: {self.format_}\n"
            f"AccessFlags: {self.accessFlags}\n"
            f"Width: {self.width}\n"
            f"Height: {self.height}\n"
            f"Depth: {self.depth}\n"
            f"Array Length: {self.arrayLength}\n"
            f"Texture Layout: {self.textureLayout}\n"
            f"Texture Layout2: {self.textureLayout2}\n"
            f"Image Size: {self.imageSize}\n"
            f"Alignment: {self.alignment}\n"
            f"Comp Sel: {self._compSel}\n"
            f"Img Dim: {self.imgDim}\n"
            f"Name Adr: {self.nameAddr}\n"
            f"Parent Adr: {self.parentAddr}\n"
            f"Ptrs Adr: {self.ptrsAddr}\n"
            f"User Data Addr: {self.userDataAddr}\n"
            f"Tex Ptr: {self.texPtr}\n"
            f"TexViewPtr: {self.texViewPtr}\n"
            f"DescSlotDataAddr: {self.descSlotDataAddr}\n"
            f"UsrDictAddr: {self.userDictAddr}\n"
        )

    def setNameIndex(self, strTbl):
        self.nameIdx = strTbl.index(self.nameAddr)

    def save(self):
        self._compSel = self.compSel[3] << 24 | self.compSel[2] << 16 | self.compSel[1] << 8 | self.compSel[0]

        if not self.readTexLayout:
            textureLayout = 0

        else:
            textureLayout = self.sparseResidency << 5 | self.sparseBinding << 4 | self.blockHeightLog2

        self.textureLayout = textureLayout
        self.flags = self.sparseResidency << 2 | self.sparseBinding << 1 | self.readTexLayout

        return struct.pack(
            self.format,
            self.flags,
            self.dim,
            self.tileMode,
            self.swizzle,
            self.numMips,
            self.numSamples,
            self.format_,
            self.accessFlags,
            self.width,
            self.height,
            self.depth,
            self.arrayLength,
            self.textureLayout,
            self.textureLayout2,
            self.imageSize,
            self.alignment,
            self._compSel,
            self.imgDim,
            self.nameAddr,
            self.parentAddr,
            self.ptrsAddr,
            self.userDataAddr,
            self.texPtr,
            self.texViewPtr,
            self.descSlotDataAddr,
            self.userDictAddr,
        )


class RelocTBL:
    class Block:
        def __init__(self, endianness):
            self.format = endianness + 'Q2I2i'
            self.basePtr = 0

        def load(self, data, pos):
            (self.basePtr,
             self.pos,
             self.size_,
             self.relocEntryIdx,
             self.relocEntryCount) = struct.unpack_from(self.format, data, pos)

        def loadEntries(self, relocEntries):
            self.entries = relocEntries[self.relocEntryIdx:self.relocEntryIdx + self.relocEntryCount]

        def save(self):
            return struct.pack(
                self.format,
                self.basePtr,
                self.pos,
                self.size_,
                self.relocEntryIdx,
                self.relocEntryCount,
            )

    class Entry:
        def __init__(self, endianness):
            self.endianness = endianness
            self.format = endianness + 'IH2B'

        def load(self, data, pos):
            (self.pos,
             self.structCount,
             self.offsetCount,
             self.paddingCount) = struct.unpack_from(self.format, data, pos)

            self.structs = []
            self.padding = self.paddingCount * 8
            pos = self.pos

            for _ in range(self.structCount):
                struct_ = []
                for _ in range(self.offsetCount):
                    struct_.append(pos)
                    pos += 8

                self.structs.append(struct_)
                pos += self.padding

        def save(self):
            self.structCount = len(self.structs)

            if self.structs:
                self.offsetCount = len(self.structs[0])

            else:
                self.offsetCount = 0

            return struct.pack(
                self.format,
                self.pos,
                self.structCount,
                self.offsetCount,
                self.paddingCount,
            )

    def __init__(self, endianness):
        self.endianness = endianness

    def load(self, data, pos, blockCount):
        self.blocks = []

        for _ in range(blockCount):
            block = self.Block(self.endianness)
            block.load(data, pos)

            self.blocks.append(block)
            pos += 0x18

        self.entries = []

        try:
            numEntries = max([block.relocEntryIdx + block.relocEntryCount for block in self.blocks])

        except ValueError:
            pass

        else:
            for _ in range(numEntries):
                entry = self.Entry(self.endianness)
                entry.load(data, pos)

                self.entries.append(entry)
                pos += 8

    def save(self):
        return b''.join([
            b''.join([block.save() for block in self.blocks]),
            b''.join([entry.save() for entry in self.entries]),
        ])


def readInt64(data, pos, endianness):
    return struct.unpack(endianness + "q", data[pos:pos + 8])[0]


def packInt64(v, endianness):
    return struct.pack(endianness + "q", v)
