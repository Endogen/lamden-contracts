I = importlib

lock_data = Hash(default_value="")

dex = Variable()
neb_base = Variable()
lock_fee = Variable()
max_lock_time = Variable()

OPERATORS = [
    'ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d',
    'e787ed5907742fa8d50b3ca2701ab8e03ec749ced806a15cdab800a127d7f863',
    '62783e94c14b0ae0c555f33ca6aa9699099606d636d4f0fd916bf912d8022045'
]

# DONE
@construct
def seed():
    lock_fee.set(1)
    max_lock_time.set(365)
    neb_base.set('con_neb_base_001')
    dex.set('con_rocketswap_official_v1_1')

# DONE
@export
def lock_lp(lock_id: str, token_contract: str, lp_amount: float, lock_time_in_days: int):
    assert lp_amount > 0, "Negative LP amount not allowed!"
    assert lock_time_in_days > 0, "Negative lock time not allowed!"
    assert lock_time_in_days <= max_lock_time.get(), f"Max lock time is {max_lock_time} days"
    assert lock_id not in lock_data, 'Lock ID already exists!'

    neb_fee = lp_amount / 100 * lock_fee.get()

    I.import_module(dex.get()).transfer_liquidity_from(
        contract=token_contract, 
        to=ctx.this, 
        main_account=ctx.caller, 
        amount=lp_amount)

    contracts = ForeignHash(foreign_contract=neb_base.get(), foreign_name='contracts')

    I.import_module(dex.get()).transfer_liquidity(
        contract=token_contract, 
        to=contracts['treasury'], 
        amount=neb_fee)

    lock_data[lock_id] = {
        "start_date": now, 
        "contract": token_contract, 
        "returned": False, 
        "amount": lp_amount - neb_fee, 
        "owner": ctx.caller, 
        "days": lock_time_in_days, 
        "dex": dex.get(), 
    }
    
    return f'{lock_data[lock_id]["start_date"] + datetime.timedelta(days=lock_data[lock_id]["days"])}'

# DONE
@export
def unlock_lp(lock_id: str):
    assert lock_id in lock_data, "Unknown lock ID!"

    lock = lock_data[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"
    assert lock["returned"] == False, "Locked LP already returned!"

    lock_end = lock["start_date"] + datetime.timedelta(days=lock["days"])

    assert now >= lock_end , f"Unlock date not reached: {lock_end}"

    I.import_module(lock["dex"]).transfer_liquidity(
        contract=lock["contract"], 
        to=lock["owner"], 
        amount=lock["amount"])

    lock["returned"] = True
    lock_data[lock_id] = lock

    return lock

# DONE
@export
def extend_time(lock_id: str, days_to_extend: int):
    assert days_to_extend > 0, "Negative time extension not allowed!"
    assert lock_id in lock_data, "Unknown lock ID!"

    lock = lock_data[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"
    assert lock["returned"] == False, "Locked LP already returned!"

    lock["days"] += days_to_extend

    error = f'Max lock time is {max_lock_time} days. You try to set {lock["days"]} days'
    assert lock["days"] <= max_lock_time.get(), error

    lock_data[lock_id] = lock

    return f'{lock["start_date"] + datetime.timedelta(days=lock["days"])}'

# DONE
@export
def extend_amount(lock_id: str, lp_amount: float):
    assert lp_amount > 0, "Negative LP amount not allowed!"
    assert lock_id in lock_data, "Unknown lock ID!"

    lock = lock_data[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"
    assert lock["returned"] == False, "Locked LP already returned!"

    neb_fee = lp_amount / 100 * lock_fee.get()

    I.import_module(dex.get()).transfer_liquidity_from(
        contract=token_contract, 
        to=ctx.this, 
        main_account=ctx.caller, 
        amount=lp_amount)

    contracts = ForeignHash(foreign_contract=neb_base.get(), foreign_name='contracts')

    I.import_module(dex.get()).transfer_liquidity(
        contract=token_contract, 
        to=contracts['treasury'], 
        amount=neb_fee)

    lock["amount"] += lp_amount - neb_fee
    lock_data[lock_id] = lock

    return lock

# DONE
@export
def time_until_unlock(lock_id: str):
    assert lock_id in lock_data, "No LP locked for this ID!"
    return f'{now - lock_data[lock_id]["start_date"]}'

@export 
def burn_lp(contract: str, amount: float):
    rswp.transfer_liquidity_from(
        contract=contract, 
        to="BURNED_LP", 
        main_account=ctx.caller, 
        amount=amount)

@export 
def burn_locked_lp(lock_id: str):
    assert lock_data[lock_id] != "", "No LP lock for this ID!"

    lock = lock_data[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"

    rswp.transfer_liquidity_from(
        contract=lock["contract"], 
        to="BURNED_LP", 
        main_account=ctx.this, 
        amount=lock["amount"])

def set_neb_base(neb_base_contract: str):
    neb_base.set(neb_base_contract)
    assert_owner()

def set_lock_fee(percent_of_lp: float):
    assert percent_of_lp >= 0, "Fee can not be negative!"
    lock_fee.set(percent_of_lp)
    assert_owner()

def set_max_lock_time(max_time_in_days: float):
    assert max_time_in_days > =, "Max lock time can not be smaller than 1 day!"
    max_lock_time.set(max_time_in_days)
    assert_owner()

def assert_owner():
    assert ctx.caller in OPERATORS, 'Only executable by operators!'
