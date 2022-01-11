extern crate keystone;

use std::fs::File;
use std::io::prelude::*;
use keystone::{Keystone, Arch, OptionType, Mode};

struct IpsEntry<'a> {
    offset: u32,
    patch: &'a [u8]
}

const TEXT_OFFSET: u32 = 0x100;

fn main() {
    let engine = Keystone::new(Arch::ARM64, Mode::LITTLE_ENDIAN)
        .expect("Could not initialize Keystone engine");
    
    let result = engine.asm("mov x1, #0x80".to_string(), 0)
        .expect("Could not assemble");

    println!("{}", result);
    
    generate_ips(&[
        IpsEntry{
            offset: 0x1433f0,
            patch: &result.bytes
        }
    ]);
}

// generation code based on rschailjker/tsukire ips_gen.cpp
// ips spec available here: https://zerosoft.zophar.net/ips.php
fn generate_ips(entries: &[IpsEntry]) -> Result<(), std::io::Error> {
    let mut fp = File::create("patch.ips")?;

    fp.write_all(b"PATCH");

    for entry in entries.iter() {
        let nso_offset = entry.offset + TEXT_OFFSET;

        // address as 24-bit BE
        fp.write_all(&[
            ((nso_offset >> 16) & 0xFF) as u8,
            ((nso_offset >> 8)  & 0xFF) as u8,
            ((nso_offset)       & 0xFF) as u8
        ]);

        // patch size 16-bit BE
        fp.write_all(&[
            ((entry.patch.len() >> 8) & 0xFF) as u8,
            ((entry.patch.len()     ) & 0xFF) as u8,
        ]);

        fp.write_all(entry.patch);
    }

    fp.write_all(b"EOF");

    Ok(())
}
