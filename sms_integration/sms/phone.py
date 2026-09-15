import phonenumbers


def to_e164(raw_number: str, default_region: str | None = None) -> str | None:
	if not raw_number:
		return None

	raw_number = raw_number.strip()

	try:
		parsed = phonenumbers.parse(raw_number, default_region)
	except phonenumbers.NumberParseException:
		return None

	if not phonenumbers.is_valid_number(parsed):
		return None

	return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
