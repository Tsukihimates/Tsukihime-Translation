use std::fs::File;
use std::io::prelude::*;

/// Set of patch bytes with an offset to insert them at
/// View the IPS spec for more information: https://zerosoft.zophar.net/ips.php
pub struct IpsEntry {
    pub offset: u32,
    pub patch: Vec<u8>
}


const TEXT_OFFSET: u32 = 0x100;

// generation code based on rschailjker/tsukire ips_gen.cpp
// ips spec available here: https://zerosoft.zophar.net/ips.php
pub fn generate_ips(entries: &[IpsEntry], result_filename: &str) -> Result<(), std::io::Error> {
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
