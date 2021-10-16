use std::convert::TryInto;
use std::io::{Error, ErrorKind, Read, Result};

pub fn read_signed(buf: &mut [u8;4], input: &mut dyn Read) -> Result<i32> {
	input.read_exact(buf)?;
	Ok(i32::from_le_bytes(*buf))
}

pub fn read_unsigned(buf: &mut [u8;4], input: &mut dyn Read) -> Result<u32> {
	input.read_exact(buf)?;
	Ok(u32::from_le_bytes(*buf))
}

pub fn read_unsigned_array(buf: &mut [u8;4], input: &mut dyn Read) -> Result<Vec<u32>> {
	let count = read_usize(buf, input)?;
	let mut vec = Vec::with_capacity(count);
	for _ in 0 .. count {
		vec.push(read_unsigned(buf, input)?);
	}
	Ok(vec)
}

pub fn read_usize(buf: &mut [u8;4], input: &mut dyn Read) -> Result<usize> {
	match read_unsigned(buf, input)?.try_into() {
		Ok(converted) => Ok(converted),
		Err(err) => Err(Error::new(ErrorKind::InvalidData, err))
	}
}

pub fn read_string(buf: &mut [u8;4], input: &mut dyn Read) -> Result<String> {
	input.read_exact(buf)?;
	let string_length = u32::from_le_bytes(*buf);
	let mut string = String::with_capacity(string_length as usize);
	input.take(string_length as u64).read_to_string(&mut string)?;
	Ok(string)
}
