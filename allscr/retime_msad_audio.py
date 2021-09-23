#!/usr/bin/env python3
import enum
import os
import re
import sys


class ScriptCommand:
    def __init__(self, opcode, arguments=None):
        # Opcode is the text keyword for this command, e.g. WKST or PGST
        # This is stored WITHOUT leading underscore
        self.opcode = opcode

        # Arguments is a list of string encoded arguments to this command
        # Arguments must be joined by commas when packing scripts
        self.arguments = arguments

    def __str__(self):
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


def process_script(timing_db, script_commands):
    # Use two lists to handle seeking without caring about indices
    # Both lists are stored in-order
    head = []
    tail = script_commands

    # When inside an active section, use a secondary buffer to track commands
    # since the search start
    seek_buf = []           # In-order temporary command buffer

    state = PState.ADVANCE
    while tail:
        if state == PState.ADVANCE:
            # Pop the first item on the tail
            cmd = tail.pop(0)

            # Is this command a special _ZM
            cmd_is_zm = cmd.opcode.startswith('ZM')
            cmd_is_zm_ke = cmd_is_zm and cmd.arguments[0].endswith('@k@e')
            cmd_is_zm_x = cmd_is_zm and cmd.arguments[0].startswith('@x')

            # If the commands is not a zm, just move it to the head list
            # and continue iterating
            if not (cmd_is_zm_ke or cmd_is_zm_x):
                head.append(cmd)
                continue

            # If this is an @x prefixed _ZM, we need to convert it to an
            # MSAD and then backtrack to find the previous _ZM
            if cmd_is_zm_x:
                cmd.opcode = 'MSAD'
                cmd.arguments[0] = re.sub("@x", "", cmd.arguments[0])
                seek_buf = [cmd]
                state = PState.X_LOOKBACK
                continue

            if cmd_is_zm_ke:
                # assert False, "Unimplemented"
                head.append(cmd)

        # Are we searching backwards for the _ZM before a lone @x?
        if state == PState.X_LOOKBACK:
            # Check that we have not fully consumed the head stack
            assert head, "Lookback reached start of script"

            # Pop the last item from the head list
            cmd = head.pop()

            # If the next command isn't a ZM, just stick it on the front of the
            # seek buffer and continue
            cmd_is_zm = cmd.opcode.startswith('ZM')
            if not cmd_is_zm:
                seek_buf.insert(0, cmd)
                continue

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
            len_delta = len(seek_buf) - target_seek_buf_len

            # If the block is too _long_, we can't really do anything
            # to fix it?
            assert len_delta <= 0, "Block too long"

            # If the block is too short, insert some 1ms WTTM to pad
            for _ in range(len_delta):
                seek_buf.insert(0, ScriptCommand("WTTM", ["1", "1"]))

            # We are done patching this block - move the entire chunk over
            # to the visited stack
            head.append(cmd)
            for c in seek_buf:
                head.append(c)

            # Move back to the ADVANCE state
            seek_buf = []
            state = PState.ADVANCE

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
