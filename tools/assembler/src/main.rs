extern crate keystone;

use std::fs::File;
use std::{i64, env};
use std::io::{self, prelude::*, BufReader};
use keystone::{Keystone, Arch, Mode};

fn main() -> io::Result<()>{
    let argv: Vec<String> = env::args().collect();

    let entries = parse_patch_file(argv[1].as_str())?;
    generate_ips(&entries, argv[2].as_str())?;

    println!("IPS Patch generated at {}", argv[2]);
    
    Ok(())
}

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
fn parse_patch_file(filename: &str) -> io::Result<Vec<IpsEntry>> {
    let mut ips_entries = Vec::<IpsEntry>::new();

    let engine = Keystone::new(Arch::ARM64, Mode::LITTLE_ENDIAN)
        .expect("Could not initialize Keystone engine");

    let file = File::open(filename)?;
    let buf_reader = BufReader::new(file);

    let mut state = ParserState::OutOfBlock;
    let mut offset: u32 = 0;
    let mut patch_bytes = Vec::<u8>::new();

    for l in buf_reader.lines() {
        let line = l?;
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

/// Set of patch bytes with an offset to insert them at
/// View the IPS spec for more information: https://zerosoft.zophar.net/ips.php
struct IpsEntry {
    offset: u32,
    patch: Vec<u8>
}

const TEXT_OFFSET: u32 = 0x100;

// generation code based on rschailjker/tsukire ips_gen.cpp
// ips spec available here: https://zerosoft.zophar.net/ips.php
fn generate_ips(entries: &[IpsEntry], result_filename: &str) -> Result<(), std::io::Error> {
    let mut fp = File::create(result_filename)?;

    fp.write_all(b"PATCH")?;

    for entry in entries.iter() {
        let nso_offset = entry.offset + TEXT_OFFSET;

        // address as 24-bit BE
        fp.write_all(&[
            ((nso_offset >> 16) & 0xFF) as u8,
            ((nso_offset >> 8)  & 0xFF) as u8,
            ((nso_offset)       & 0xFF) as u8
        ])?;

        // patch size 16-bit BE
        fp.write_all(&[
            ((entry.patch.len() >> 8) & 0xFF) as u8,
            ((entry.patch.len()     ) & 0xFF) as u8,
        ])?;

        fp.write_all(&entry.patch)?;
    }

    fp.write_all(b"EOF")?;

    Ok(())
}
