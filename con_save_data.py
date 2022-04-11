data = Hash(default_value='')

@export
def save(key: str, value: str):
	data[key] = value
