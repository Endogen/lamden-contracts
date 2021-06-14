data = Hash()

@export
def lock(contract: str, amount: float, minutes: int):
	# Check that amount is not negative
	assert amount > 0, "Cannot lock negative amount"

	# Import token contract
	asset = importlib.import_module(contract)

	# Generate ID
	uid = hashlib.sha256(str(now))

	# Check that ID is unique
	assert not data[uid], "ID is not unique"

	# Generate timedelta for locking timeframe
	lock = datetime.timedelta(minutes=minutes)

	# Save details about lock
	data[uid] = {
		"payed": False,
		"asset": contract,
		"owner": ctx.signer,
		"start": now,
		"amount": amount,
		"unlock": now + lock
	}

	# Send amount to contract address to lock it
	asset.transfer_from(amount=amount, to=ctx.this, main_account=ctx.signer)

	# Return ID for this lock
	return uid

@export
def unlock(uid: str):
	# Check if ID is known
	assert data[uid], "ID not found"
	# Check if lock was already payed
	assert data[uid]["payed"] is False, "Already payed out"
	# Check if caller is owner of locked amount
	assert ctx.caller == data[uid]["owner"], "Only owner can unlock funds"
	# Check if locked amount can be released
	assert now > data[uid]["unlock"], "Unlock date not reached"

	# Import token contract
	asset = importlib.import_module(data[uid]["asset"])

	# Pay out locked amount
	asset.transfer(amount=data[uid]["amount"], to=ctx.caller)

	# Mark as payed
	data[uid]["payed"] = True

@export
def info(uid: str):
	# Check if ID is known
	assert data[uid], "ID not found"

	if uid:
		# Return info about lock with given ID
		return data[uid]
	else:
		# Return info about all locks
		return data