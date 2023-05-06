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


def process_script_file(scene_name_map,
                        script_filename, output_filename):
    print(script_filename)

    # Work out what mrg entry this is / what the scene names is
    match = re.search(r".*/allscr.mrg_(\d+).txt", script_filename)
    scene_idx = int(match.group(1))
    scene_name = scene_name_map[scene_idx]
    print(scene_name)

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
        script_commands
    )

    # Is this a QA scene?
    # If it is, we want to excise _all_ newline triggers in _ZM calls
    is_qa = scene_name.startswith('QA_')
    if is_qa:
        new_cmds = []
        for cmd in script_commands:
            if cmd.opcode.startswith('ZM'):
                print(cmd)
                cmd.arguments[0] = cmd.arguments[0].replace('^@n', '@n')
            new_cmds.append(cmd)
        script_commands = new_cmds

    # Serialize it back out over the input file
    with open(output_filename, 'w') as f:
        for cmd in script_commands:
            f.write(str(cmd) + "\n")


class PState(enum.Enum):
    ADVANCE = 1
    KE_SEEK_VPLY = 2
    KE_SEEK_X = 3
    X_SEEK_WKAD = 4


def patch_ke_x_block(script_commands):
    # Given a block that starts with a _ZM(@k@e) and ends with a _ZM(@x),
    # mutate the block according to our rules.
    # print("Patch ke block. Raw:")
    # print([str(c) for c in script_commands])

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
    # print("KE blocks:")
    # print(blocks)
    # print("Final block:")
    # print(current_block)

    # Append the final block
    blocks.append(current_block)

    # Process each @k@e block
    def process_block(block):
        # Add an @n in the ZM block to auto-trigger the next line
        if not block[0].opcode.startswith('ZM'):
            print("Invalid start of block: %s" % block[0].opcode)
            return block

        # print("Start of block: %s" % (block[0]))
        block[0].arguments[0] = re.sub("@k@e", "@k@e@n", block[0].arguments[0])

        # Change any WKAD(F823, 1) to WKAD(F823, 0)
        for i in range(len(block)):
            if block[i].opcode == 'WKAD' and block[i].arguments[0] == 'F823':
                block[i].arguments[1] = '0'

        return block

    blocks = [process_block(b) for b in blocks]

    # For all @k@e blocks other than the _first_ @k@e block, change the
    # _ZM to a _MSAD
    first_msad_block = 2 if blocks[0][0].opcode == 'VPLY' else 1
    for block in blocks[first_msad_block:]:
        block[0].opcode = 'MSAD'
        block[0].arguments[0] = re.sub("@x", "", block[0].arguments[0])

    # Flatten the blocks back into a list & return
    ret = []
    for block in blocks:
        for c in block:
            ret.append(c)

    # print("Processed cmds:")
    # print(ret)
    return ret


def process_script(script_commands):
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

            # Is this a compound ZM (QA section)
            if cmd_is_zm:
                split_args = cmd.arguments[0].split('^')
                has_args = len(split_args) > 1
                if has_args and all([c[0] == '$' for c in split_args]):
                    # Replace this ZM with a ZM + MSADs
                    head.append(ScriptCommand(
                        cmd.opcode, [split_args[0]+"@n"]))
                    if len(split_args) > 2:
                        for c in split_args[1:-1]:
                            head.append(ScriptCommand('MSAD', [c+"@n"]))
                    head.append(ScriptCommand('MSAD', [split_args[-1]]))
                    continue

            # If the commands is not a zm, just move it to the head list
            # and continue iterating
            if not (cmd_is_ke or cmd_is_x):
                head.append(cmd)
                continue

            # If this is an @x prefixed _ZM, we need to convert it to an
            # MSAD and strip the @x. We also need to seek backwards to the
            # preceding WKAD(F823,1) and s/1/0
            if cmd_is_x:
                print("Encountered non-ke @x: %s" % cmd)
                cmd.opcode = 'MSAD'
                cmd.arguments[0] = re.sub("@x", "", cmd.arguments[0])
                seek_buf = [cmd]
                state = PState.X_SEEK_WKAD
                continue

            # If this is a _ZM with an @k@e sequence, we need to do two things:
            # - Seek _backwards_ to find the voice line for the @k@e ZM
            # - Seek _forwards_ to find a terminating _ZM(@x)
            if cmd_is_ke:
                seek_buf = [cmd]
                state = PState.KE_SEEK_VPLY
                continue

            assert False, "Unexpected end of PState.ADVANCE"

        # Are we searching backwards for the WKAD preceing a standalone @x?
        if state == PState.X_SEEK_WKAD:
            if not head:
                print("Hit SOF trying to match WKAD to @x, skipping")
                # Glue buffered commands back onto head
                for c in seek_buf:
                    head.append(c)

                # return to ADVANCE state
                state = PState.ADVANCE
                continue

            # If we still have commands to search, pop one
            cmd = head.pop(-1)
            cmd_is_wkad = cmd.opcode == 'WKAD'

            # If it's a different text line or we hit a pagebreak, bail out
            cmd_is_pgst = cmd.opcode == 'PGST'
            cmd_is_msad = cmd.opcode == 'MSAD'
            cmd_is_zm = cmd.opcode.startswith('ZM')
            if cmd_is_pgst or cmd_is_msad or cmd_is_zm:
                print("Hit page/text trying to match WKAD to @x, skipping")
                # Glue buffered commands back onto head
                for c in seek_buf:
                    head.append(c)

                # return to ADVANCE state
                state = PState.ADVANCE
                continue

            # If it's not WKAD, prepend to seek buf and continue
            if not cmd_is_wkad:
                seek_buf.insert(0, cmd)
                continue

            # If it is WKAD, but wrong flag, continue
            if cmd.arguments[0] != 'F823':
                seek_buf.insert(0, cmd)
                continue

            # If it is WKAD and _right_ flag, force the argument to zero
            cmd.arguments[1] = '0'

            # Flush seek buffer and return to SEEK
            head.append(cmd)
            for c in seek_buf:
                head.append(c)
            state = PState.ADVANCE
            continue

        # Are we searching backwards for a VPLY that associates to an @k@e ZM?
        if state == PState.KE_SEEK_VPLY:
            if not head:
                print("Hit EOF trying to match VPLY to @k@e, skipping WTTM")
                # Glue buffered commands back onto head _except_ for the KE cmd
                for c in seek_buf[:-1]:
                    head.append(c)
                seek_buf = [seek_buf[-1]]

                # Go to KE second stage, SEEK_X
                state = PState.KE_SEEK_X
                continue

            # If we still have commands to search, pop one
            cmd = head.pop(-1)
            cmd_is_pgst = cmd.opcode == 'PGST'
            cmd_is_zm = cmd.opcode.startswith('ZM')
            if cmd_is_pgst or cmd_is_zm:
                # If we get a page turn, or a different text line, then
                # presumably there is no VPLY to glue.
                print("Hit PGST/ZM trying to match VPLY to @k@e, skip WTTM")
                # Glue buffered commands back onto head _except_ for the KE cmd
                head.append(cmd)
                for c in seek_buf[:-1]:
                    head.append(c)
                seek_buf = [seek_buf[-1]]

                # Go to KE second stage, SEEK_X
                state = PState.KE_SEEK_X
                continue

            # If it's not a cmd that causes us to break, just add it to seek
            # buf and continue
            cmd_is_vply = cmd.opcode == 'VPLY'
            if not cmd_is_vply:
                seek_buf.insert(0, cmd)
                continue

            # If it _is_ the VPLY we were looking for, stick it on the seek buf
            # and move to the next state.
            seek_buf.insert(0, cmd)
            state = PState.KE_SEEK_X
            continue

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

            # Push this command onto the seek buf
            seek_buf.append(cmd)

            # If this command is a _repeated_ @k@e, keep going
            if cmd.arguments[0].endswith('@k@e'):
                continue

            # If we have found the final @x, go patch up the block
            processed_block = patch_ke_x_block(seek_buf)
            for c in processed_block:
                head.append(c)

            # Move back to ADVANCE
            state = PState.ADVANCE
            continue

    assert(not tail)
    return head


def load_nam_file(filename):
    # Nam files are simple enough to parse in python, just split into
    # 32 byte chunks and strip any \0
    with open(filename, 'rb') as f:
        data = f.read()

    entries = [data[i:i+32] for i in range(0, len(data), 32)]

    print(entries)

    return {
        i + 3: ''.join([chr(c) for c in entries[i] if c != 0]).strip()
        for i in range(len(entries))
    }


def main():
    # Check arguments
    if len(sys.argv) != 4:
        sys.stderr.write(
            f"Usage: {sys.argv[0]} nam_file "
            f"script_dir output_dir\n")
        return -1

    # Name args
    nam_filename = sys.argv[1]
    script_dir_path = sys.argv[2]
    output_path = sys.argv[3]

    # Parse the NAM file to get a map of MRG entry number to scene name
    scene_name_map = load_nam_file(nam_filename)

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
            scene_name_map,
            dirent.path,
            os.path.join(output_path, dirent.name)
        )


if __name__ == "__main__":
    main()
