use std::fmt;
use std::io::{Error, ErrorKind, Result, Read, Write};

use super::Faction;
use super::readhelpers::*;


#[derive(PartialEq)]
pub enum Field {
	Float(f32),
	Integer(i32),
	Reference(String),
	String(String)
}

impl fmt::Debug for Field {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		match self {
			Field::Reference(value) => {
				fmt.write_str("#")?;
				value.fmt(fmt)
			}
			Field::Float(value) => value.fmt(fmt),
			Field::Integer(value) => value.fmt(fmt),
			Field::String(value) => value.fmt(fmt)
		}
	}
}


#[derive(PartialEq)]
pub struct EntityGroup {
	pub faction: Faction,
	pub entity_type: u32,
	pub entities: Vec<Entity>
}

impl EntityGroup {
	pub (crate) fn deserialize(input: &mut dyn Read) -> Result<EntityGroup> {
		let mut word_buffer = [0;4];
		let faction = Faction::from(read_unsigned(&mut word_buffer, input)?);
		let entity_type = read_unsigned(&mut word_buffer, input)?;
		let entity_count = read_usize(&mut word_buffer, input)?;
		let mut entities = Vec::with_capacity(entity_count);
		for _ in 0 .. entity_count {
			entities.push(Entity::deserialize(input)?);
		}
		Ok(EntityGroup {faction, entity_type, entities})
	}

	pub (crate) fn serialize(&self, w: &mut dyn Write) -> Result<usize> {
		let mut len = 0;
		len += w.write(&u32::from(self.faction).to_le_bytes())?;
		len += w.write(&self.entity_type.to_le_bytes())?;
		len += w.write(&(self.entities.len() as u32).to_le_bytes())?;
		for e in &self.entities {
			len += e.serialize(w)?;
		}
		Ok(len)
	}
}

impl fmt::Debug for EntityGroup {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		fmt.write_fmt(format_args!("EntityGroup {{faction: {:?}, entity_type: {:?}, entities: [", self.faction, self.entity_type))?;
		if !self.entities.is_empty() {
			for entity in &self.entities {
				fmt.write_fmt(format_args!("\n\t{:?}", entity))?;
			}
			fmt.write_str("\n")?;
		}
		fmt.write_str("]}")
	}
}


#[derive(Debug, PartialEq)]
pub struct Entity {
	pub name: String,
	pub research: Vec<u32>,
	pub fields: Vec<Field>
}

impl Entity {
	fn deserialize(input: &mut dyn Read) -> Result<Entity> {
		let mut word_buffer = [0;4];
		let name = read_string(&mut word_buffer, input)?;
		let research = read_unsigned_array(&mut word_buffer, input)?;

		let field_count = read_usize(&mut word_buffer, input)?;
		let mut field_types = vec![0;field_count];
		input.read_exact(&mut field_types)?;

		let mut fields: Vec<Field> = Vec::with_capacity(field_count);
		for field_type in field_types {
			let field = read_field(&mut fields, field_type != 0, &mut word_buffer, input)?;
			fields.push(field);
		}

		Ok(Entity {name, research, fields})
	}

	fn serialize(&self, w: &mut dyn Write) -> Result<usize> {
		let mut len = 0;
		len += write_string(w, &self.name)?;
		len += w.write(&(self.research.len() as u32).to_le_bytes())?;
		for r in &self.research {
			len += w.write(&r.to_le_bytes())?;
		}
		let mut field_count: u32 = 0;
		for f in &self.fields {
			field_count += match f {
				Field::Reference(_) => 2,
				_ => 1
			}
		}
		len += w.write(&field_count.to_le_bytes())?;
		for f in &self.fields {
			len += match f {
				Field::String(_) => w.write(&[1])?,
				Field::Reference(_) => w.write(&[1, 0])?,
				_ => w.write(&[0])?
			};
		}
		for e in &self.fields {
			len += match e {
				Field::Float(value) => w.write(&value.to_le_bytes())?,
				Field::Integer(value) => w.write(&value.to_le_bytes())?,
				Field::Reference(value) => write_string(w, value)? + w.write(&(-1i32).to_le_bytes())?,
				Field::String(value) => write_string(w, value)?
			};
		}
		Ok(len)
	}
}

fn read_field(fields: &mut Vec<Field>, is_string: bool, buf: &mut[u8;4], input: &mut dyn Read) -> Result<Field> {
	if is_string {
		Ok(Field::String(read_string(buf, input)?))
	} else {
		let value = read_signed(buf, input)?;
		if value == -1 && matches!(fields.last(), Some(Field::String(_))) {
			// Pop the string off and replace it with a reference with the same value
			if let Some(Field::String(value)) = fields.pop() {
				Ok(Field::Reference(value))
			} else {
				// Should never happen since this was just checked
				Err(Error::new(ErrorKind::InvalidData, "String somehow changed to nonstring value"))
			}
		} else {
			Ok(Field::Integer(value))
		}
	}
}

fn write_string(w: &mut dyn Write, value: &String) -> Result<usize> {
	Ok(w.write(&(value.len() as u32).to_le_bytes())?
		+ w.write(value.as_bytes())?)
}
