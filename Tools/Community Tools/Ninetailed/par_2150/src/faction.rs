use std::fmt;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Faction {
	Neutral,
	UCS,
	LC,
	ED
}

impl From<u32> for Faction {
	fn from(value: u32) -> Faction {
		match value {
			1 => Faction::UCS,
			2 => Faction::ED,
			3 => Faction::LC,
			_ => Faction::Neutral
		}
	}
}

impl fmt::Display for Faction {
	fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
		fmt.write_str(match self {
			Faction::UCS => "UCS",
			Faction::ED => "ED",
			Faction::LC => "LC",
			_ => "Neutral"
		})
	}
}

impl From<Faction> for u32 {
	fn from(value: Faction) -> u32 {
		match value {
			Faction::UCS => 1,
			Faction::ED => 2,
			Faction::LC => 3,
			_ => 0
		}
	}
}
