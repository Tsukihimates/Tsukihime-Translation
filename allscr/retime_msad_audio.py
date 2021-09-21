#!/usr/bin/env python3
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
        return "%s(%s);" % (self.opcode, ','.join(self.arguments or []))


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


def process_script_file(audio_timing, script_filename):
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

    # Finally, we get to the good part - seek through our file until we find
    # a _ZM* opcode that contains @k@e in the address section.
    for zm_cmd_idx in range(len(script_commands)):
        zm_cmd = script_commands[zm_cmd_idx]
        if not zm_cmd.opcode.startswith("ZM"):
            # Not a _ZM call, ignore
            continue

        # Does this ZM call have an argument?
        if len(zm_cmd.arguments) != 1:
            # Unexpected - _ZM should only take one argument
            sys.stderr.write("Unexpected _ZM arguments: '%s'\n" % str(zm_cmd))
            continue

        # Does that _ZM contain an @k@e escape sequence?
        if not zm_cmd.arguments[0].endswith('@k@e'):
            # No escape sequence, ignore
            continue

        # At this point, we have a _ZM command that comtains our target
        sys.stderr.write("[%s] Located _ZM call '%s' @ +%d\n" % (
            script_filename, str(zm_cmd), zm_cmd_idx
        ))

        # escape sequence. Seek forwards until we find the next _ZM
        found_valid_next_zm = False
        for subsequent_zm_idx in range(zm_cmd_idx + 1, len(script_commands)):
            subsequent_zm_cmd = script_commands[subsequent_zm_idx]
            if not subsequent_zm_cmd.opcode.startswith("ZM"):
                # Not a _ZM call, ignore
                continue

            # Found our next _ZM - does the argument start with an @x modifier?
            has_right_cmd_len = len(subsequent_zm_cmd.arguments) == 1
            if (not has_right_cmd_len
                    or not subsequent_zm_cmd.arguments[0].startswith("@x")):
                sys.stderr.write(
                    "[%s]    Secondary _ZM instruction '%s' "
                    "does not start with @x\n" % (
                        script_filename,
                        str(subsequent_zm_cmd)
                    )
                )
                found_valid_next_zm = False
                break

            # If it does, this is the line we need to modify.
            found_valid_next_zm = True
            break

        # If we couldn't find a valid next zm, do not attempt to patch up this
        # command pair
        if not found_valid_next_zm:
            sys.stderr.write("[%s]     Failed to locate secondary _ZM\n" % (
                script_filename
            ))
            continue

        # If we did, print some info
        sys.stderr.write("[%s]     Located secondary %s @ +%d\n" % (
            script_filename, str(subsequent_zm_cmd), subsequent_zm_idx
        ))

        # Now that we have the two bounding _ZM calls, seek _backwards_ from
        # the secondary _ZM until we hit a VPLY call for the corresponding
        # voice line


def main():
    # Check arguments
    if len(sys.argv) != 3:
        sys.stderr.write(
            f"Usage: {sys.argv[0]} audio_timing script_directory\n")
        return -1

    # Name args
    audio_timing_filename = sys.argv[1]
    script_dir_path = sys.argv[2]

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

        # Process the file. Note that we rewrite it IN PLACE; be sure to use
        # version control!
        process_script_file(audio_timing, dirent.path)


if __name__ == "__main__":
    main()
