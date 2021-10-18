import con_amm_v9 as rswp

lock_info = Hash(default_value="")

@export
def lock_lp(contract: str, amount: float, lock_time_in_days: int):
    assert amount > 0, "Negative amount not allowed!"
    assert lock_time_in_days > 0, "Negative lock time not allowed!"

    lock_time = datetime.timedelta(days=lock_time_in_days)
    lock_id = hashlib.sha256(f"{ctx.caller}{now}")
    
    rswp.transfer_liquidity_from(
        contract=contract, 
        to=ctx.this, 
        main_account=ctx.caller, 
        amount=amount)

    lock_info[lock_id] = {
        "owner": ctx.caller, 
        "start_date": now, 
        "contract": contract, 
        "amount": amount, 
        "days": lock_time_in_days
    }
    
    return f"Lock ID: {lock_id}"
 
@export
def unlock_lp(lock_id: str):
    assert lock_info[lock_id] != "", "No LP lock for this ID!"

    lock = lock_info[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"

    lock_end = lock["start_date"] + datetime.timedelta(days=lock["days"])

    assert now >= lock_end , f"LP lock date not reached: {lock_end}"

    rswp.transfer_liquidity(
        contract=lock["contract"], 
        to=ctx.caller, 
        amount=lock["amount"])

    return lock
    
@export
def extend_time(lock_id: str, days_to_extend: int):
    assert days_to_extend > 0, "Negative time not allowed!"
    assert lock_info[lock_id] != "", "No LP lock for this ID!"

    lock = lock_info[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"

    lock["days"] += days_to_extend
    lock_info[lock_id] = lock

    return f"Lock time extended by {days_to_extend} days"

@export
def extend_amount(lock_id: str, amount: float):
    assert amount > 0, "Negative amount not allowed!"
    assert lock_info[lock_id] != "", "No LP lock for this ID!"

    lock = lock_info[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"

    rswp.transfer_liquidity_from(
        contract=lock["contract"], 
        to=ctx.this, 
        main_account=ctx.caller, 
        amount=amount)

    lock["amount"] += amount
    lock_info[lock_id] = lock

    return f"Lock amount extended by {amount}"


@export
def time_until_unlock(lock_id: str):
    assert lock_info[lock_id] != "", "No LP lock for this ID!"
    return now - lock_info[lock_id]["start_date"]

@export 
def burn_lp(contract: str, amount: float):
    rswp.transfer_liquidity_from(
        contract=contract, 
        to="BURNED_LP", 
        main_account=ctx.caller, 
        amount=amount)

@export 
def burn_locked_lp(lock_id: str):
    assert lock_info[lock_id] != "", "No LP lock for this ID!"

    lock = lock_info[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"

    rswp.transfer_liquidity_from(
        contract=lock["contract"], 
        to="BURNED_LP", 
        main_account=ctx.this, 
        amount=lock["amount"])
