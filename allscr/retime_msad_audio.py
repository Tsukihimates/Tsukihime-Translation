#!/usr/bin/env python3
import enum
import os
import re
import sys


#  11.ext: Standalone @x with VPLY
#  58.txt: @k@e with no @x before EOF
# 107.txt: Standalone @x with no VPLY
# 147.txt: _MSAD with @k@e sequence


class ScriptCommand:
    def __init__(self, opcode, arguments=None):
        # Opcode is the text keyword for this command, e.g. WKST or PGST
        # This is stored WITHOUT leading underscore
        self.opcode = opcode

        # Arguments is a list of string encoded arguments to this command
        # Arguments must be joined by commas when packing scripts
        self.arguments = arguments

    def __repr__(self):
        # Convert a script command to a string for emission
        return "_%s(%s);" % (self.opcode, ','.join(self.arguments or []))


def load_timing(filename):
    audio_timing = {}
    with open(filename, "r") as f:
        # Read in the file
        data = f.read()

        # Iterate each line
        for line in data.split('\n'):
            # Remove any leading/trailing spaces
            stripped = line.strip()

            # If the line is now empty, just ignore it
            if not stripped:
                continue

            # Split the line on : to get name and time
            line_parts = stripped.split(":")
            if len(line_parts) != 2:
                sys.stderr.write(f"Ignoring invalid input line '{stripped}'\n")
                continue

            # Emplace data into our map
            audio_timing[line_parts[0]] = int(line_parts[1])

    return audio_timing


def process_script_file(audio_timing, script_filename, output_filename):
    print(script_filename)

    # Load in the raw script
    file_data_raw = None
    with open(script_filename, "r") as f:
        file_data_raw = f.read()

    # Split into commands on semicolon and discard any empty lines
    script_commands_raw = [
        line.strip()
        for line in file_data_raw.split(";")
        if line.strip()
    ]

    # Regex to match our script commands. This regex defines two match
    # groups - the opcode (group 0), and the contained arguments as a single
    # string (group 1).
    # For commands that do not have arguments, there will be no second
    # match group
    command_regex = re.compile(r"_(\w+)\(([\w 　a-zA-Z0-9-,`@$:.+^_]*)\)\Z")

    # Parse each of our script commands into a command struct
    script_commands = []
    for line in script_commands_raw:
        # Regex out our command name and arguments
        match = command_regex.match(line)
        groups = match.groups()
        script_commands.append(
            ScriptCommand(groups[0])
            if len(groups) == 1
            else ScriptCommand(groups[0], groups[1].split(','))
        )

    # Perform our transforms on the script
    # - Take all @k@e -> @x pairs, and convert to a _ZM + _WTTM + _MSAD
    script_commands = process_script(
        audio_timing,
        script_commands
    )

    # Serialize it back out over the input file
    with open(output_filename, 'w') as f:
        for cmd in script_commands:
            f.write(str(cmd) + "\n")


class PState(enum.Enum):
    ADVANCE = 1
    X_LOOKBACK = 2
    KE_SEEK_X = 3
    KE_PROCESS = 4


def patch_ke_x_block(timing_db, script_commands):
    # Given a block that starts with a _ZM(@k@e) and ends with a _ZM(@x),
    # mutate the block according to our rules.
    print("Patch ke block. Raw:")
    print([str(c) for c in script_commands])

    # split the cmd_block into a list of chunks, where each chunk starts with
    # a _ZM(@k@e) and ends with the command right before the next text output
    # cmd. We should end up with at least 2 blocks for the single @k@e case
    # (second block has @x cmd and nothing else) and more than 2 blocks for the
    # repeated @k@e case
    blocks = []
    current_block = [script_commands.pop(0)]
    while script_commands:
        # Pop front
        cmd = script_commands.pop(0)

        # If this isn't a ZM, append to current block
        cmd_is_zm = cmd.opcode.startswith('ZM')
        if not cmd_is_zm:
            current_block.append(cmd)
            continue

        # If it is a ZM, end the current block and begin new block
        blocks.append(current_block)
        current_block = [cmd]

    # Once we are done processing, blocks contains a list of one or more ke
    # blocks, and the current block _should_ contain a single @x ZM command
    assert len(blocks) >= 1
    assert len(current_block) == 1
    print("KE blocks:")
    print(blocks)
    print("Final block:")
    print(current_block)

    # Append the final block
    blocks.append(current_block)

    # Process each @k@e block
    def process_block(block):
        # Get the length of the block for sanity checking
        block_len = len(block)

        # Convert @k@e -> @n in the _ZM command args
        block[0].arguments[0] = re.sub("@k@e", "@n", block[0].arguments[0])

        # Is there a VPLY?
        found_vplys = [c for c in block if c.opcode == 'VPLY']
        if found_vplys:
            vply = found_vplys[0]
            delay_ms = timing_db[vply.arguments[0]]
            wttm = ScriptCommand("WTTM", [str(delay_ms), "1"])
            block.insert(1, wttm)

        # Delete any WKAD(F823)
        block = [
            c for c in block
            if not (c.opcode == 'WKAD' and c.arguments[0] == 'F823')
        ]

        # Are we now over/under the target length for this block
        len_delta = block_len - len(block)
        print(f"Len delta: {len_delta}")
        print([str(c) for c in block])

        # If the block is too _long_, we can't really do anything
        # to fix it?
        assert len_delta >= 0, "Block too long"

        # If the block is too short, insert some 1ms WTTM to pad
        for _ in range(len_delta):
            block.insert(1, ScriptCommand("WTTM", ["1", "1"]))

        return block

    blocks = [process_block(b) for b in blocks]

    # For all @k@e blocks other than the _first_ @k@e block, change the
    # _ZM to a _MSAD
    for block in blocks[1:]:
        block[0].opcode = 'MSAD'
        block[0].arguments[0] = re.sub("@x", "", block[0].arguments[0])

    # Flatten the blocks back into a list & return
    ret = []
    for block in blocks:
        for c in block:
            ret.append(c)

    print("Processed cmds:")
    print(ret)
    return ret


def process_script(timing_db, script_commands):
    # Use two lists to handle seeking without caring about indices
    # Both lists are stored in-order
    head = []
    tail = script_commands

    # When inside an active section, use a secondary buffer to track commands
    # since the search start
    seek_buf = []           # In-order temporary command buffer

    state = PState.ADVANCE
    while True:
        if state == PState.ADVANCE:
            # If the tail is empty, the loop is done
            if not tail:
                break

            # Pop the first item on the tail
            cmd = tail.pop(0)

            # Is this command a special _ZM
            cmd_is_zm = cmd.opcode.startswith('ZM')
            cmd_is_msad = cmd.opcode == 'MSAD'
            is_txt_cmd = cmd_is_zm or cmd_is_msad
            cmd_is_ke = is_txt_cmd and cmd.arguments[0].endswith('@k@e')
            cmd_is_x = is_txt_cmd and cmd.arguments[0].startswith('@x')

            # If the commands is not a zm, just move it to the head list
            # and continue iterating
            if not (cmd_is_ke or cmd_is_x):
                head.append(cmd)
                continue

            # If this is an @x prefixed _ZM, we need to convert it to an
            # MSAD and then backtrack to find the previous _ZM
            if cmd_is_x:
                cmd.opcode = 'MSAD'
                cmd.arguments[0] = re.sub("@x", "", cmd.arguments[0])
                seek_buf = [cmd]
                state = PState.X_LOOKBACK
                continue

            # If this is a _ZM with an @k@e sequence, we need to start
            # seeking forward until we find a terminating _ZM(@x)
            if cmd_is_ke:
                seek_buf = [cmd]
                state = PState.KE_SEEK_X
                continue

            assert False, "Unexpected end of PState.ADVANCE"

        # Are we searching forward as part of a KE block for a terminating @x?
        if state == PState.KE_SEEK_X:
            # If we hit the end of the file, don't try and modify this block?
            if not tail:
                print("Hit EOF trying to match @k@e, no changes made")
                # Move all the data that were in the seek buf to head
                for c in seek_buf:
                    head.append(c)

                # return to ADVANCE state
                state = PState.ADVANCE
                continue

            # Pop the first item on the tail
            cmd = tail.pop(0)

            # If we don't have a match, append to seek buf and continue
            cmd_is_zm = cmd.opcode.startswith('ZM')
            if not cmd_is_zm:
                seek_buf.append(cmd)
                continue

            # If this is a ZM, but doesn't have @x, don't modify this block?
            # TODO(ross) confirm with Hakanaou
            cmd_is_zm_x = cmd_is_zm and cmd.arguments[0].startswith('@x')
            if not cmd_is_zm_x:
                for c in seek_buf:
                    head.append(c)
                head.append(cmd)

                # Move back to the ADVANCE state
                state = PState.ADVANCE
                continue

            # If we have found the final @x, push it onto the seek buffer and
            # then go patch up the block in another function
            seek_buf.append(cmd)
            processed_block = patch_ke_x_block(timing_db, seek_buf)
            for c in processed_block:
                head.append(c)

            # Move back to ADVANCE
            state = PState.ADVANCE
            continue

        # Are we searching backwards for the _ZM before a lone @x?
        if state == PState.X_LOOKBACK:
            # Check that we have not fully consumed the head stack
            assert head, "Lookback reached start of script"

            # Pop the last item from the head list
            cmd = head.pop()

            # If the next command isn't a ZM, just stick it on the front of the
            # seek buffer and continue
            cmd_is_zm = cmd.opcode.startswith('ZM')
            cmd_is_msad = cmd.opcode == 'MSAD'
            if not (cmd_is_zm or cmd_is_msad):
                seek_buf.insert(0, cmd)
                continue

            print("Patch @x block:")
            print([str(c) for c in seek_buf])

            # We have found the preceding _ZM - we now need to
            # - Insert a WTTM with the length of first VPLY after the ZM
            # - Delete all WKAD(F823) in the seek buffer
            # - If we have deleted more than one WKAD, insert dummy 1ms
            #   WTTM calls so that the total number of instructions line up

            # Mark how many commands we have so we can keep it the same
            target_seek_buf_len = len(seek_buf)

            # Did we find any VPLYs to insert timing for?
            found_vplys = [c for c in seek_buf if c.opcode == 'VPLY']
            if found_vplys:
                vply = found_vplys[0]
                delay_ms = timing_db[vply.arguments[0]]
                wttm = ScriptCommand("WTTM", [str(delay_ms), "1"])
                seek_buf.insert(0, wttm)

            # Iterate the seek buf and delete any WKAD(F823)
            seek_buf = [
                c for c in seek_buf
                if not (c.opcode == 'WKAD' and c.arguments[0] == 'F823')
            ]

            # Are we now over/under the target length for this block
            len_delta = target_seek_buf_len - len(seek_buf)
            print(f"Len delta: {len_delta}")
            print([str(c) for c in seek_buf])

            # If the block is too _long_, we can't really do anything
            # to fix it?
            assert len_delta >= 0, "Block too long"

            # If the block is too short, insert some 1ms WTTM to pad
            for _ in range(len_delta):
                seek_buf.insert(0, ScriptCommand("WTTM", ["1", "1"]))

            # We are done patching this block - move the entire chunk over
            # to the visited stack
            head.append(cmd)
            for c in seek_buf:
                head.append(c)

            # Move back to the ADVANCE state
            state = PState.ADVANCE
            continue

    assert(not tail)
    return head


def main():
    # Check arguments
    if len(sys.argv) != 4:
        sys.stderr.write(
            f"Usage: {sys.argv[0]} audio_timing script_dir output_dir\n")
        return -1

    # Name args
    audio_timing_filename = sys.argv[1]
    script_dir_path = sys.argv[2]
    output_path = sys.argv[3]

    # Load in the timing file to a map of filename -> time (ms)
    audio_timing = load_timing(audio_timing_filename)

    # Now, iterate each of the .txt files in the decompressed script directory
    # and patch up any @k@e + @x pairs
    for dirent in os.scandir(script_dir_path):
        # Ignore directories
        if not dirent.is_file:
            continue

        # Ignore non-txt files
        if not dirent.path.endswith(".txt"):
            continue

        # Process the file, and write to the output directory
        process_script_file(
            audio_timing,
            dirent.path,
            os.path.join(output_path, dirent.name)
        )


if __name__ == "__main__":
    main()
