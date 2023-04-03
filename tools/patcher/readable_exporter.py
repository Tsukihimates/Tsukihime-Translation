class ReadableExporter:
    """
    Human-readable export format is as follows:

    // Each line context block is opened with a
    [baa173e] { // Where the value in the [] is the content hash of a jp line
    // Any lines prefixed with a '//' are kept as human readable comments
    -- Any lines prefixed with a '--' are automatically generated comments,
    -- and will not be re-imported to the comment field
    Any lines that are not prefixed with a comment marker are considered to
    be translated text.

    // Comments may be interspersed with the translation, either on their own line
    This is translation text// Or after a specific line of the translation
    // However, when imported and reexported, all comments will be consolidated at
    // the top of the context block.

    If the translated text spans multiple lines, those line breaks _WILL NOT_ be
    included when the text is imported.

        Note that _leading_ spaces are not stripped from translation lines

    However, _trailing_ spaces WILL be stripped. Account for manual spacing only
    at the front of translations.
    }
    """

    class ParseError(Exception):
        def __init__(self, *args, **kwargs):
            super(ReadableExporter.ParseError, self).__init__(*args, **kwargs)

    class LexState:
        EXPECT_BLOCK = 0
        PARSE_BLOCK_PREFIX = 1
        PARSE_BLOCK_ID = 2
        EXPECT_OPEN_BLOCK = 3
        DEFAULT_BLOCK = 4
        PARSE_MACHINE_COMMENT = 5
        PARSE_HUMAN_COMMENT = 6

    class Diff:
        class EntryGroup:
            def __init__(self):
                self.entries = []

            def __repr__(self):
                return f"EntryGroup({self.entries})"

            def add_entry(self, entry):
                self.entries.append(entry)

            def is_unique(self):
                if not self.entries:
                    return True

                # If any entries don't match, non-unique
                expect_en = self.entries[0].en_text
                expect_comment = self.entries[0].comment
                for i in range(1, len(self.entries)):
                    if self.entries[i].en_text != expect_en or \
                       self.entries[i].comment != expect_comment:
                        return False

                return True

        class Entry:
            def __init__(self, filename, line, en_text, comment):
                self.filename = filename
                self.line = line
                self.en_text = en_text
                self.comment = comment

            def __repr__(self):
                return (
                    f"Diff.Entry(filename='{self.filename}', "
                    f"line={self.line}, en_text='{self.en_text}', "
                    f"comment='{self.comment}')"
                )

        def __init__(self):
            # Map of sha to list of entry
            self.entries_by_sha = {}
            self.entries_by_offset = {}

        def __repr__(self):
            ret = "Diff("
            for sha, entries in self.entries_by_sha.items():
                ret += f"sha:{sha}: {entries}, "
            for offset, entries in self.entries_by_offset.items():
                ret += f"offset:{offset}: {entries}, "
            return ret

        def any_conflicts(self):
            for entry_group in self.entries_by_sha.values():
                if not entry_group.is_unique():
                    return True

            return False

        def add_sha_entry(self, sha, filename, line, en_text, comment):
            if sha not in self.entries_by_sha:
                self.entries_by_sha[sha] = self.EntryGroup()

            self.entries_by_sha[sha].add_entry(self.Entry(
                filename,
                line,
                en_text,
                comment
            ))

        def add_offset_entry(self, offset, filename, line, en_text, comment):
            if offset not in self.entries_by_offset:
                self.entries_by_offset[offset] = self.EntryGroup()

            self.entries_by_offset[offset].add_entry(self.Entry(
                filename,
                line,
                en_text,
                comment
            ))

        def append_diff(self, other):
            for sha in other.entries_by_sha:
                if sha not in self.entries_by_sha:
                    self.entries_by_sha[sha] = self.EntryGroup()
                for entry in other.entries_by_sha[sha].entries:
                    self.entries_by_sha[sha].add_entry(entry)
            for offset in other.entries_by_offset:
                if offset not in self.entries_by_offset:
                    self.entries_by_offset[offset] = self.EntryGroup()
                for entry in other.entries_by_offset[offset].entries:
                    self.entries_by_offset[offset].add_entry(entry)

    @classmethod
    def import_text(cls, filename):
        ret = cls.Diff()

        # Read the file data
        with open(filename, 'rb') as f:
            file_text = f.read().decode('utf-8')

        state = cls.LexState.EXPECT_BLOCK
        cmd_acc = ""
        active_content_hash = None
        active_block_is_offset_override = False
        line_counter = 1
        brace_count = 0
        translated_text = ""
        human_comments = ""
        block_start_line = None
        for i in range(len(file_text)):
            c = file_text[i]
            if c == '\n':
                line_counter += 1

            # Are we waiting for the start of a block?
            if state == cls.LexState.EXPECT_BLOCK:
                # Ignore whitespace
                if c in "\r\n ":
                    continue

                # If we get an open content hash spec '[', transition states
                if c == '[':
                    state = cls.LexState.PARSE_BLOCK_PREFIX
                    cmd_acc = ""
                    continue

                raise cls.ParseError(
                    f"Unexpected token '{c}' on "
                    f"line {line_counter} while in state EXPECT_BLOCK"
                )

            # Accumulate the sha: or offset: prefix on the block
            if state == cls.LexState.PARSE_BLOCK_PREFIX:
                # Ignore whitespace
                if c in "\r\n ":
                    continue

                # Delimiter?
                if c == ':':
                    if cmd_acc == "sha":
                        active_block_is_offset_override = False
                    elif cmd_acc == "offset":
                        active_block_is_offset_override = True
                    else:
                        raise cls.ParseError(
                            f"Invalid block prefix tag '{cmd_acc}'"
                        )

                    state = cls.LexState.PARSE_BLOCK_ID
                    cmd_acc = ""
                    continue

                # Accumulate the character onto the cmd_acc buffer
                cmd_acc += c

            # Are we processing the content-hash specifier for a block?
            if state == cls.LexState.PARSE_BLOCK_ID:
                # Ignore whitespace
                if c in "\r\n ":
                    continue

                # End of block?
                if c == ']':
                    # Hit the end of the [] block - the accumulator now holds
                    # the content hash context for the next scoped region.
                    state = cls.LexState.EXPECT_OPEN_BLOCK
                    active_content_hash = cmd_acc
                    cmd_acc = ""
                    continue

                if active_block_is_offset_override:
                    # Offsets must be pure numeric
                    if c not in '0123456789':
                        raise cls.ParseError(
                            f"Invalid character '{c}' in "
                            f"offset on line {line_counter}"
                        )
                if not active_block_is_offset_override:
                    # All content hashes must be valid lowercase hex
                    if c not in '0123456789abcdef':
                        raise cls.ParseError(
                            f"Invalid character '{c}' in "
                            f"content hash on line {line_counter}"
                        )

                # Accumulate the character onto the cmd_acc buffer
                cmd_acc += c

            # Consume whitespace chars until we get to an open-brace
            if state == cls.LexState.EXPECT_OPEN_BLOCK:
                # Ignore whitespace
                if c in "\r\n ":
                    continue

                # Open block?
                if c == '{':
                    # Now properly inside a context block
                    brace_count += 1
                    state = cls.LexState.DEFAULT_BLOCK
                    block_start_line = line_counter
                    cmd_acc = ""
                    continue

                raise cls.ParseError(
                    "Expected open-block after block-specifier "
                    f"but found '{c}' on line {line_counter}"
                )

            # Consume until we hit a close-block '}'. Accumulate lines into
            # cmd_acc until we hit either a newline or comment char, at which
            # point we would latch the buffer and transition to the next
            # appropriate state
            if state == cls.LexState.DEFAULT_BLOCK:
                # Hit a newline?
                if c == '\n':
                    # If there is a valid line in the input buffer, add it to
                    # the translation text
                    # Preserve line breaks in the source text so that we can
                    # re-export stably, even though these line breaks will NOT
                    # be respected by the injector
                    rstrip_acc = cmd_acc.rstrip()
                    if rstrip_acc:
                        translated_text += \
                            ("\n" if translated_text else "") + rstrip_acc
                    # Reset the accumulator
                    cmd_acc = ""
                    continue

                # Track open-brace chars so that if any show up in the
                # translated text we match them and don't get confused
                if c == '{':
                    brace_count += 1

                # Hit an end-brace?
                if c == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # This is a terminating brace - process the accumulated
                        # command buffer and transition back to default state
                        rstrip_acc = cmd_acc.rstrip()
                        if rstrip_acc:
                            translated_text += rstrip_acc
                        cmd_acc = ""

                        # If this line was useless (no comment, no tl)
                        # just don't even bother to include it
                        if not translated_text and not human_comments:
                            translated_text = ""
                            human_comments = ""
                            # Move back to default state
                            state = cls.LexState.EXPECT_BLOCK
                            continue

                        # Create a new entry in our return map
                        # If there is no valid tl or comments, use None instead
                        # of empty string as an indicator
                        if active_block_is_offset_override:
                            ret.add_offset_entry(
                                int(active_content_hash),
                                filename,
                                line_counter,
                                translated_text or None,
                                human_comments or None
                            )
                        else:
                            ret.add_sha_entry(
                                active_content_hash,
                                filename,
                                line_counter,
                                translated_text or None,
                                human_comments or None
                            )
                        translated_text = ""
                        human_comments = ""

                        # Move back to default state
                        state = cls.LexState.EXPECT_BLOCK
                        continue

                # Is this the second char in a -- quote?
                if c == '-' and cmd_acc and cmd_acc[-1] == '-':
                    # Bank any translation text, excluding the prev '-'
                    rstrip_acc = cmd_acc[:-1].rstrip()
                    if rstrip_acc:
                        translated_text += rstrip_acc
                    cmd_acc = ""

                    # Open machine comment context
                    state = cls.LexState.PARSE_MACHINE_COMMENT
                    continue

                # Is this the second char in a // quote?
                if c == '/' and cmd_acc and cmd_acc[-1] == '/':
                    # Bank any translation text, excluding prev '/'
                    rstrip_acc = cmd_acc[:-1].rstrip()
                    if rstrip_acc:
                        translated_text += rstrip_acc
                    cmd_acc = ""

                    # Open human comment context
                    state = cls.LexState.PARSE_HUMAN_COMMENT
                    continue

                # If nothing special is going on, just add this char to the buf
                cmd_acc += c

            # Currently reading a machine comment. Discard until we see EOL
            if state == cls.LexState.PARSE_MACHINE_COMMENT:
                if c == '\n':
                    state = cls.LexState.DEFAULT_BLOCK
                    cmd_acc = ""

            # Currently reading a human comment. Accumulate characters until
            # we hit EOL, then append to comment block
            if state == cls.LexState.PARSE_HUMAN_COMMENT:
                if c == '\n':
                    # If the comment was non-empty, save it
                    strip_acc = cmd_acc.strip()
                    if strip_acc:
                        human_comments += strip_acc + "\n"
                    cmd_acc = ""

                    state = cls.LexState.DEFAULT_BLOCK
                    continue

                # Append the character to the cmd_buf
                cmd_acc += c

        # If we exit the parser and are still inside a block, that's
        # a parse error
        if state == cls.LexState.DEFAULT_BLOCK:
            raise cls.ParseError(
                f"Unterminated line block on {filename}:{block_start_line}")

        return ret
