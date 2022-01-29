use std::env;
use std::io;

mod parser;
mod ips;

fn main() -> io::Result<()>{
    let argv: Vec<String> = env::args().collect();

    let entries = parser::parse_patch_file(argv[1].as_str())?;
    ips::generate_ips(&entries, argv[2].as_str())?;

    println!("IPS Patch generated at {}", argv[2]);
    
    Ok(())
}
