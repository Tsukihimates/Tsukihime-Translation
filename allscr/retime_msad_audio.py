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
    script_commands = squash_ke_to_msad(
        audio_timing,
        script_filename,
        script_commands
    )

    # - Delete any remaining @x prefixes on _ZM calls
    script_commands = replace_standalone_zm_x_msad(script_commands)

    # Serialize it back out over the input file
    with open(output_filename, 'w') as f:
        for cmd in script_commands:
            f.write(str(cmd) + "\n")


def replace_standalone_zm_x_msad(script_commands):
    for idx in range(len(script_commands)):
        zm_cmd = script_commands[idx]
        if not zm_cmd.opcode.startswith("ZM"):
            # Not a _ZM call, ignore
            continue

        # Does this ZM call have an argument?
        if len(zm_cmd.arguments) != 1:
            # Unexpected - _ZM should only take one argument
            sys.stderr.write("Unexpected _ZM arguments: '%s'\n" % str(zm_cmd))
            continue

        # Is that _ZM prefixed with an @x escape sequence?
        if not zm_cmd.arguments[0].startswith('@x'):
            # No escape sequence, ignore
            continue

        # Delete the @x prefix
        script_commands[idx].arguments[0] = \
            zm_cmd.arguments[0] = re.sub("@x", "", zm_cmd.arguments[0])

        # Change the opcode to MSAD
        script_commands[idx].opcode = "MSAD"

    return script_commands


def squash_ke_to_msad(audio_timing, script_filename, script_commands):
    # Start seeking through our file until we find a _ZM* opcode that
    # contains @k@e in the address section.
    zm_cmd_idx = -1
    while True:
        # The 'pythonic' way to do a for loop is to iterate a generator, but
        # since we need to do a bunch of index manipulation while we
        # add / remove script entries, manually implement a more flexible
        # C-style for loop.
        zm_cmd_idx += 1
        if not zm_cmd_idx < len(script_commands):
            break

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

        # In some cases, the script may have multiple _ZM(@k@e) sequences in a
        # row before we get to a _ZM(@x) sequence. Store the indices of these
        # instaces so that we can patch them up once we have found the
        # terminating @x entry
        repeated_ke_idxs = []

        # escape sequence. Seek forwards until we find the next _ZM
        found_valid_next_zm = False
        for next_zm_idx in range(zm_cmd_idx + 1, len(script_commands)):
            next_zm_cmd = script_commands[next_zm_idx]
            if not next_zm_cmd.opcode.startswith("ZM"):
                # Not a _ZM call, ignore
                continue

            # Found our next _ZM - does the argument start with an @x modifier?
            has_right_cmd_len = len(next_zm_cmd.arguments) == 1
            if not has_right_cmd_len:
                sys.stderr.write(
                    "[%s]     Secondary _ZM instruction '%s' "
                    "has incorrect argument count\n" % (
                        script_filename,
                        str(next_zm_cmd)
                    )
                )
                found_valid_next_zm = False
                break

            # Is this a repeated @k@e?
            if next_zm_cmd.arguments[0].endswith('@k@e'):
                # Save this one in our list for later
                repeated_ke_idxs.append(next_zm_idx)
                continue

            # Do we have an @x?
            found_valid_next_zm = next_zm_cmd.arguments[0].startswith("@x")
            break

        # If we couldn't find a valid next zm, do not attempt to patch up this
        # command pair
        if not found_valid_next_zm:
            sys.stderr.write("[%s]     Failed to locate secondary _ZM\n" % (
                script_filename
            ))
            continue

        # If we did, print some info
        if repeated_ke_idxs:
            sys.stderr.write("[%s]     Repeated @k@e sequences: %s\n" % (
                script_filename, repeated_ke_idxs
            ))
        sys.stderr.write("[%s]     Located secondary %s @ +%d\n" % (
            script_filename, str(next_zm_cmd), next_zm_idx
        ))

        # For each non-terminal _ZM, seek forwards to the next VPLY and extract
        # play time so that we can add a delay before triggering the next text
        vply_wait_by_ke_idx = {}
        for repeat_idx in repeated_ke_idxs:
            # Scan forward until we hit a VPLY or another text line
            vply_idx = repeat_idx
            while True:
                vply_idx += 1
                if vply_idx >= len(script_commands):
                    break
                vply_cmd = script_commands[vply_idx]

                # If we find a _ZM before we found a VPLY, then there is no
                # audio to add a wait for.
                if vply_cmd.opcode.startswith("_ZM"):
                    break

                # Ignore non-VPLY commands
                if not vply_cmd.opcode == "VPLY":
                    # Not a _VPLY call, ignore
                    continue

                # If we find a VPLY command, assert that it has 2 arguments
                if len(vply_cmd.arguments) != 2:
                    sys.stderr.write(
                        "[%s]     Associated VPLY @ +%d invalid: '%s'\n" % (
                            script_filename, vply_idx, str(vply_cmd)
                        )
                    )
                    break

                # If we found a valid VPLY, load the timing data
                if vply_cmd.arguments[0] not in audio_timing:
                    sys.stderr.write(
                        "[%s]     Missing audio timing data for file %s\n" % (
                            script_filename, str(vply_cmd)
                        )
                    )
                    break

                # Insert this timing into our map
                vply_wait_by_ke_idx[repeat_idx] = \
                    audio_timing[vply_cmd.arguments[0]]

        # We have valid timing data - now that we have gathered our
        # prerequisites, it is time to make our modifications.
        # - Replace @k@e with @n on all _ZM calls
        for idx in repeated_ke_idxs + [zm_cmd_idx]:
            script_commands[idx].arguments[0] = \
                re.sub("@k@e", "@n", script_commands[idx].arguments[0])

        # Replace the opcode on all intermediate + end _ZM calls with _MSAD
        for idx in repeated_ke_idxs + [next_zm_idx]:
            # Delete @x from arguments on intermediate calls
            script_commands[idx].arguments[0] = re.sub(
                "@x", "", script_commands[idx].arguments[0])

            # MSAD not _ZM
            script_commands[idx].opcode = "MSAD"

        # For each _ZM call, if we found a subsequent _VPLY, add a _WTTM
        # to match the delays up.
        # Perform these inserts in reverse so that we don't mess up the indexes
        for idx in sorted(vply_wait_by_ke_idx.keys(), reverse=True):
            script_commands.insert(
                idx + 1,
                ScriptCommand(
                    "WTTM",
                    [str(vply_wait_by_ke_idx[idx]), "1"]
                )
            )
            sys.stderr.write(
                "[%s]     Inserted WTTM of len %d for %s @ +%d\n" % (
                    script_filename, vply_wait_by_ke_idx[idx],
                    vply_cmd.arguments[0], idx+1
                )
            )

        # At this point, we have mutated the list - we need to regenerate the
        # offsets for all _ZM calls other than the first one. Each index is
        # offset by the total number of WTTM calls that were injected before it
        adjusted_ke_idxs = []
        for idx in repeated_ke_idxs:
            # We inserted a WTTM for every valid VPLY that came before the
            # original index location of this entry
            prev_wttm_count = len([
                k for k in vply_wait_by_ke_idx.keys() if k < idx
            ])
            adjusted_ke_idxs.append(idx + prev_wttm_count)

        # With our patched up offsets, we can now delete the WKAD/WKST calls
        # Iterate backwards again so that mutating the script list doesn't
        # indexing on us during the operation

        for remove_idx in range(next_zm_idx - 1, zm_cmd_idx, -1):
            if script_commands[remove_idx].opcode in ["WKAD", "WNTY", "WKST"]:
                # It seems that we need to keep WKST calls that set the flag
                # C847, which may affect where choices jump you in the script.
                # If we see one of these, leave it alone.
                is_wkst = script_commands[remove_idx].opcode == "WKST"
                wkst_is_c847 = (
                    len(script_commands[remove_idx].arguments) and
                    script_commands[remove_idx].arguments[0] == "C847"
                )
                if is_wkst and wkst_is_c847:
                    continue

                # Otherwise, delete
                del script_commands[remove_idx]

    # Finally, we have our modified script.
    return script_commands


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
