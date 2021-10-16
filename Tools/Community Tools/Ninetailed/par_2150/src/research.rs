use std::io::{Result, Read, Write};

use super::faction::Faction;
use super::readhelpers::*;


#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Research {
	pub research: Vec<u32>,
	pub id: u32,
	pub faction: Faction,
	pub campaign_cost: u32,
	pub skirmish_cost: u32,
	pub campaign_time: u32,
	pub skirmish_time: u32,
	pub name: String,
	pub video: String,
	pub tab: u32,
	pub mesh: String,
	pub mesh_params_index: u32
}

impl Research {
	pub (crate) fn deserialize(input: &mut dyn Read) -> Result<Research> {
		let mut word_buffer = [0;4];
		Ok(Research {
			research: read_unsigned_array(&mut word_buffer, input)?,
			id: read_unsigned(&mut word_buffer, input)?,
			faction: Faction::from(read_unsigned(&mut word_buffer, input)?),
			campaign_cost: read_unsigned(&mut word_buffer, input)?,
			skirmish_cost: read_unsigned(&mut word_buffer, input)?,
			campaign_time: read_unsigned(&mut word_buffer, input)?,
			skirmish_time: read_unsigned(&mut word_buffer, input)?,
			name: read_string(&mut word_buffer, input)?,
			video: read_string(&mut word_buffer, input)?,
			tab: read_unsigned(&mut word_buffer, input)?,
			mesh: read_string(&mut word_buffer, input)?,
			mesh_params_index: read_unsigned(&mut word_buffer, input)?
		})
	}

	pub (crate) fn serialize(&self, w: &mut dyn Write) -> Result<usize> {
		let mut len = 0;
		len += w.write(&(self.research.len() as u32).to_le_bytes())?;
		for r in &self.research {
			len += w.write(&r.to_le_bytes())?;
		}
		len += w.write(&self.id.to_le_bytes())?;
		len += w.write(&u32::from(self.faction).to_le_bytes())?;
		len += w.write(&self.campaign_cost.to_le_bytes())?;
		len += w.write(&self.skirmish_cost.to_le_bytes())?;
		len += w.write(&self.campaign_time.to_le_bytes())?;
		len += w.write(&self.skirmish_time.to_le_bytes())?;
		len += w.write(&(self.name.len() as u32).to_le_bytes())?;
		len += w.write(self.name.as_bytes())?;
		len += w.write(&(self.video.len() as u32).to_le_bytes())?;
		len += w.write(self.video.as_bytes())?;
		len += w.write(&self.tab.to_le_bytes())?;
		len += w.write(&(self.mesh.len() as u32).to_le_bytes())?;
		len += w.write(self.mesh.as_bytes())?;
		len += w.write(&self.mesh_params_index.to_le_bytes())?;
		Ok(len)
	}
}
