extern crate par_2150;

use par_2150::*;

use std::io::Read;
use std::fs::File;

fn main() {
	let filename: &str = "C:\\Games\\Earth 2150 - The Moon Project\\WDFiles\\Parameters\\Earth2150.par";
	let mut buf: Vec<u8> = vec!();
	let len = File::open(filename).unwrap().read_to_end(&mut buf).unwrap();
	let mut buf2 = Vec::with_capacity(len);
	let result = Parameters::from_par_file(&mut buf.as_slice());
	match result {
		Err(error) => println!("{}", error),
		Ok(parameters) => {
			let len2 = parameters.to_par_file(&mut buf2).unwrap();
			println!("{} {}", len, len2);
			for i in 0 .. len2 {
				if buf[i] != buf2[i] {
					println!("First difference at {:x}: {:02x} {:02x}", i, buf[i], buf2[i]);
					break;
				}
			}
			println!("{} {}", parameters.entity_groups.len(), parameters.research.len());
		}
	}
	let par2 = Parameters::from_par_file(&mut buf2.as_slice()).unwrap();
	println!("{} {}", par2.entity_groups.len(), par2.research.len());
}
