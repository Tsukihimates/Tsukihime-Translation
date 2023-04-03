#!/usr/bin/env python3

import hashlib
import sys
import struct

from readable_exporter import ReadableExporter


def rebuild_sysmes(old_sysmes_path, translation_path, new_sysmes_path):
    # Read the packed binary of the old sysmes text
    with open(old_sysmes_path, 'rb') as sysmes:
        old_data = sysmes.read()

    # Load the EN version of the strings as a Readable diff
    translation_diff = ReadableExporter.import_text(translation_path)

    # output of new sysmes here
    new_sysmes = open(new_sysmes_path, 'wb')

    # File structure
    # 0x0: Magic? 1
    # 0x4: Total string count, u32le
    # 0x8, 0xC, 0x10, 0x14: ??
    # 0x18: String offsets start, u64le
    # (0x18 + string_count * 8): String data start
    # Post-string data: unknown footer

    # Read fixed size header
    _magic, string_count, _u1, _u2, string_data_start = \
            struct.unpack("<IIQQQ", old_data[0:32])
    print(f"Total string count: {string_count}")
    print(f"String data start offset: {string_data_start}")

    # Parse off all the string offsets
    jp_string_offsets = []
    for i in range(string_count):
        offset_loc = 0x18 + (i * 8)
        (offset,) = struct.unpack("<Q", old_data[offset_loc:offset_loc+8])
        jp_string_offsets.append(offset)

    # Get all of the strings for those offsets. Strings are terminated by '\0'
    jp_strings = []
    for offset in jp_string_offsets:
        i = offset
        while old_data[i] != 0x0:
            i += 1

        jp_strings.append(old_data[offset:i].decode('utf-8'))

    # Locate the footer by jumping to the start of the last string,
    # skipping til we hit \0, then snipping to EOF
    footer_start = jp_string_offsets[-1]
    while old_data[footer_start] != 0x0:
        footer_start += 1
    # Advance past the '\0'
    footer_start += 1

    print(f"Footer start: {footer_start}")
    footer = old_data[footer_start:]

    # Now that we have all the JP strings, go through and map them to EN strings
    # using the readable diff
    en_strings = []
    for jp in jp_strings:
        sha = hashlib.sha1(jp.encode('utf-8')).hexdigest()
        if sha not in translation_diff.entries_by_sha:
            raise Exception(f"Failed to find translation for sha {sha}: '{jp}'")
        entry_group = translation_diff.entries_by_sha[sha]
        en_text = entry_group.entries[0].en_text
        en_strings.append(en_text)

    # Alright, time to start rebuilding the EN version.
    # First, copy the fixed header across, it's all the same
    new_sysmes.write(old_data[0:0x18])

    # Now, write all the string offsets
    output_string_offset = 0x18 + string_count * 8
    for string in en_strings:
        new_sysmes.write(struct.pack("<Q", output_string_offset))
        output_string_offset += len(string.encode('utf-8')) + 1

    # Following the jump table, spurt out all those translated strings
    # Include a \0 terminator after each one
    for string in en_strings:
        new_sysmes.write(string.encode('utf-8'))
        new_sysmes.write(b"\x00")

    # Finally, slap that old footer on there
    new_sysmes.write(footer)

    # All done
    new_sysmes.close()


def main():
    rebuild_sysmes(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3]
    )


if __name__ == '__main__':
    main()
