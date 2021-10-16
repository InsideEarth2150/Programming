use std::io::{Error, ErrorKind, Read, Result, Write};

mod entity;
mod faction;
mod research;
mod readhelpers;

pub use entity::*;
pub use faction::*;
pub use research::*;
use readhelpers::*;

pub struct Parameters {
	pub entity_groups: Vec<EntityGroup>,
	pub research: Vec<Research>
}

impl Parameters {
	pub fn from_par_file(input: &mut dyn Read) -> Result<Parameters> {
			let mut header = [0;8];
			input.read_exact(&mut header)?;
			if header != [0x50, 0x41, 0x52, 0x00, 0x99, 0x00, 0x00, 0x00] {
				return Err(Error::new(ErrorKind::InvalidData, "Invalid PAR file header"));
			}

			let mut word_buffer = [0;4];
			let group_count = read_usize(&mut word_buffer, input)?;
			read_unsigned(&mut word_buffer, input)?;
			
			let mut entity_groups = Vec::with_capacity(group_count);
			for _ in 0 .. group_count {
				entity_groups.push(EntityGroup::deserialize(input)?);
			}
			
			let research_count = read_usize(&mut word_buffer, input)?;
			let mut research = Vec::with_capacity(research_count);
			for _ in 0 .. research_count {
				research.push(Research::deserialize(input)?);
			}
			Ok(Parameters{entity_groups, research})
	}

	pub fn to_par_file(&self, w: &mut dyn Write) -> Result<usize> {
		let mut len = w.write(&[0x50, 0x41, 0x52, 0x00, 0x99, 0x00, 0x00, 0x00])?;
		len += w.write(&(self.entity_groups.len() as u32).to_le_bytes())?;
		len += w.write(&[0x00, 0x00, 0x00, 0x00])?;
		for grp in &self.entity_groups {
			len += grp.serialize(w)?;
		}
		len += w.write(&(self.research.len() as u32).to_le_bytes())?;
		for r in &self.research {
			len += r.serialize(w)?;
		}
		len += w.write(&[0x01, 0x00, 0x00, 0x00])?;
		len += w.write(&(self.research.len() as u32 - 1).to_le_bytes())?;
		Ok(len)
	}
}
