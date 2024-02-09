#!/usr/bin/env python3

import argparse
import hashlib
import sys
import struct

from readable_exporter import ReadableExporter

class SysmesString:

    FLOWCHART_WIDTH = 33

    def __init__(self, text, is_flowchart_title=False,
                 is_flowchart_descr=False):
        self._text = text
        self._is_flowchart_title = is_flowchart_title
        self._is_flowchart_descr = is_flowchart_descr

    def __repr__(self):
        return f"SysmesString({self._text})"

    def raw_text(self):
        return self._text

    def is_flowchart_title(self):
        return self._is_flowchart_title

    def is_flowchart_descr(self):
        return self._is_flowchart_descr

    def formatted_text(self):
        # If this is a flowchart title, just assert that it's not too long
        if self._is_flowchart_title:
            assert self.unicode_aware_len(self._text) <= self.FLOWCHART_WIDTH, \
                f"Title too long: {self._text}"
            return self._text

        # If this is a flowchart descr, run a full linebreak process
        if self._is_flowchart_descr:
            linebroken = self.linebreak_text(self._text, self.FLOWCHART_WIDTH)
            linecount = len(linebroken.split('^'))
            # We shrunk the box back down, assert nothing gets too big
            assert linecount < 7
            return linebroken

        # Else, return string as-is
        return self._text

    @staticmethod
    def unicode_aware_len(string):
        # Any non-ASCII character takes up 2 spaces instead of one.
        length = 0
        for c in string:
            # PUA codes are treated as single-width
            if ord(c) >= 0xE000:
                length += 1
            # All non-EASCII is double-wide
            elif ord(c) > 256:
                length += 2
            else:
                length += 1

        return length

    @classmethod
    def linebreak_text(cls, text, cols):
        # First, if the text already has preprogrammed breaks, split those up
        # so we respect them. Also remove any \n characters, since those are
        # only used for human convenience.
        lines = text.replace('\n', '').split('^')
        linebroken_lines = []
        for line in lines:
            words = line.split(' ')
            current_line = ''
            for word in words:
                # Can we append to the current line?
                cur_line_len = cls.unicode_aware_len(current_line)
                word_len = cls.unicode_aware_len(word)
                if not current_line:
                    current_line = word
                elif cur_line_len + 1 + word_len <= cls.FLOWCHART_WIDTH:
                    current_line += ' ' + word
                else:
                    # If not, push back and start a new line
                    linebroken_lines.append(current_line)
                    current_line = word

            # If we have an incomplete line, append it now
            linebroken_lines.append(current_line)

        # Linebroken lines should now have a series of short lines, join them
        # all with carets
        return '^'.join(linebroken_lines)

    @staticmethod
    def diff_has_flag(diff, flag):
        if not diff.comment:
            return False
        return flag in diff.comment

    @classmethod
    def parse(cls, diff_entry):
        is_flowchart_title = cls.diff_has_flag(diff_entry, '@flowchart_title')
        is_flowchart_descr = cls.diff_has_flag(diff_entry, '@flowchart_desc')
        return cls(
            diff_entry.en_text,
            is_flowchart_title=is_flowchart_title,
            is_flowchart_descr=is_flowchart_descr
        )


def load_translated_strings(translation_path):
    # Load the EN version of the strings as a Readable diff
    translation_diff = ReadableExporter.import_text(translation_path)

    # For each string, parse control codes and make a map of sha:SysmesString
    strings_by_sha = {}
    for sha, entry_group in translation_diff.entries_by_sha.items():
        strings_by_sha[sha] = SysmesString.parse(entry_group.entries[0])

    return strings_by_sha


def rebuild_sysmes(old_sysmes_path, translation_path, new_sysmes_path):
    # Read the packed binary of the old sysmes text
    with open(old_sysmes_path, 'rb') as sysmes:
        old_data = sysmes.read()

    # Load the EN version of the strings as a Readable diff
    translations_by_sha = load_translated_strings(translation_path)

    # output of new sysmes here
    new_sysmes = open(new_sysmes_path, 'wb')

    # File structure
    # 0x0: Number of languages, u32le
    # 0x4: Total string count, u32le
    # (0x10 — 0x10 + 8 * langs): Start addresses of languages offsets, u64le
    # (0x10 + 8 * langs): The beginning of first language offsets, u64le
    # (0x10 + 8 * langs + 8 * langs * string_count): String data start
    # Post-string data: unknown footer

    # Read fixed size header
    langs, string_count = struct.unpack("<II", old_data[0:8])
    
    print(f"Number of languages: {langs}")
    print(f"Total string count: {string_count}")

    for i in range(langs):
        (offset), = struct.unpack("<Q", old_data[16+8*langs+8*i*string_count:16+8*langs+8*i*string_count+8])
        print(f"Language {i} data start offset: {offset}")

    # Parse off all the string offsets

    lang = [[]*i for i in range(langs)]
    
    for n in range(langs):
        string_offsets = []
        for i in range(string_count):
            offset_loc = 16+8*langs+8*n*string_count + (i * 8)
            (offset,) = struct.unpack("<Q", old_data[offset_loc:offset_loc+8])
            string_offsets.append(offset)
        
        # Get all of the strings for those offsets. Strings are terminated by '\0'
        strings = []
        for offset in string_offsets:
            i = offset
            while old_data[i] != 0x0:
                i += 1
            strings.append(old_data[offset:i].decode('utf-8'))
        lang[n].append(string_offsets)
        lang[n].append(strings)

    # Locate the footer by jumping to the start of the last string,
    # skipping til we hit \0, then snipping to EOF
    footer_start = lang[-1][0][-1]
    while old_data[footer_start] != 0x0:
        footer_start += 1
    # Advance past the '\0'
    footer_start += 1

    print(f"Footer start: {footer_start}")
    footer = old_data[footer_start:]

    # Now that we have all the JP strings, go through and map them to EN strings
    # using the readable diff
    en_strings = []
    for jp in lang[0][1]:
        sha = hashlib.sha1(jp.encode('utf-8')).hexdigest()
        if sha not in translations_by_sha:
            raise Exception(f"Failed to find translation for sha {sha}: '{jp}'")
        en_text = translations_by_sha[sha].formatted_text()
        en_strings.append(en_text)

    # Alright, time to start rebuilding the EN version.
#    langs = 2 # 2 langs
    new_sysmes.write(struct.pack("<I", langs))
    new_sysmes.write(old_data[4:16])

    for i in range(langs):
        new_sysmes.write(struct.pack("<Q", 16+8*langs+8*i*string_count))

    # Now, write all the string offsets
    output_string_offset = 16 + 8 * langs * (1 + string_count)
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


def lint_sysmes(translation_path):
    translations_by_sha = load_translated_strings(translation_path)
    lint_ok = True
    for sha, string in translations_by_sha.items():
        if string.is_flowchart_title():
            if len(string.raw_text()) > SysmesString.FLOWCHART_WIDTH:
                print(f"Flowchart title too long: '{string.raw_text()}'")
                lint_ok = False

    if not lint_ok:
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sysmes CLI"
    )

    # Everything needs to know this
    parser.add_argument(
        '--translation',
        dest='translation_path',
        action='store',
        help="Path to the translated strings"
    )

    # Inject args
    parser.add_argument(
        '--inject',
        dest='do_inject',
        action='store_true',
        help="Inject the current translation mrg"
    )
    parser.add_argument(
        '--base-mrg',
        dest='base_mrg_path',
        action='store',
        help="Path to base sysmes mrg",
    )
    parser.add_argument(
        '--inject-output',
        dest='inject_output',
        action='store',
        help="Where to write the translated mrg"
    )

    # Lint args
    parser.add_argument(
        '--lint',
        dest='do_lint',
        action='store_true',
        help='Assert that the translated strings are valid'
    )

    return parser.parse_args(sys.argv[1:])


def main():
    args = parse_args()
    if args.do_lint:
        lint_sysmes(args.translation_path)

    if args.do_inject:
        rebuild_sysmes(
            args.base_mrg_path,
            args.translation_path,
            args.inject_output
        )


if __name__ == '__main__':
    main()
