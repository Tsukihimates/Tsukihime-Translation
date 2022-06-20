extern crate keystone;

use std::fs::File;
use std::io::{self, prelude::*, BufReader};
use keystone::{Keystone, Arch, Mode};

use crate::ips::IpsEntry;

#[derive(Clone, Copy)]
enum ParserState {
    OutOfBlock,
    InBlock
}

/// Parse a patch file in the following format to generate IPS entries:
/// ;; comments on lines
/// 0xXXXXXX
/// INSTRUCTION+
/// ;; comments go anywhere
/// end
///
/// Note that there are no end of line comments because that would
/// just be one extra complication.
pub fn parse_patch_file(filename: &str) -> io::Result<Vec<IpsEntry>> {
    let mut ips_entries = Vec::<IpsEntry>::new();

    let engine = Keystone::new(Arch::ARM64, Mode::LITTLE_ENDIAN)
        .expect("Could not initialize Keystone engine");

    let file = File::open(filename)?;
    let buf_reader = BufReader::new(file);

    let mut state = ParserState::OutOfBlock;
    let mut offset: u32 = 0;
    let mut patch_bytes = Vec::<u8>::new();

    for l in buf_reader.lines() {
        let mut line = l?;
        // skip comments
        if line.starts_with(';') { continue; }

        match state {
            ParserState::OutOfBlock => {
                if line.starts_with("0x") {
                    offset = i64::from_str_radix(&line[2..], 16).unwrap() as u32;
                    state = ParserState::InBlock;
                    continue;
                }
            },

            ParserState::InBlock => {
                if line == "end" {
                    state = ParserState::OutOfBlock;
                    // build the result based on the current
                    // entries in the bytes vector. Copied
                    // so that the buffer can be cleared.
                    ips_entries.push(IpsEntry{
                        offset,
                        patch: patch_bytes.clone(),
                    });

                    patch_bytes.clear();
                    continue;
                }

                // parse pseudo-instruction macro for `call'
                // if future pseudo-instructions are needed (complex macros etc.)
                // this should be factored out into a match jump table.
                if line.starts_with("call") {
                    line = parse_call_statement(&line, offset + patch_bytes.len() as u32, true);
                }

                // Similar macro for calling without linking
                if line.starts_with("jump") {
                    line = parse_call_statement(&line, offset + patch_bytes.len() as u32, false);
                }

                let assembled = engine.asm(line, 0)
                    .expect("Failed to assemble");

                // patch bytes is aggregated until new set is reached
                // and then its cleared.
                patch_bytes.extend_from_slice(&assembled.bytes);
            },
        }
    }

    Ok(ips_entries)
}

/// Implementation of a fake version of `call' just to make it easier
/// to parse branch-with-link instructions to absolute addresses.
/// Obviously makes our patches non-portable, and is a little bit like #define BEGIN {,
/// but if we really need to port our patches, we can just write a little script to do
/// the necessary subtractions.
///
/// Note: All call macros are expected to be prefixed with the immediate #.
/// Example: call #0x13cc8c
fn parse_call_statement(instr: &str, instr_address: u32, link: bool) -> String {
    let dest_address = i64::from_str_radix(&instr[8..], 16).unwrap() as i32;

    let jump: i32 = dest_address - (instr_address as i32);

    return format!(
        "{} #{}{:#x}",
        if link {"bl"} else {"b"},
        if jump > 0 { "" } else { "-" },
        jump.abs()
    );
}
