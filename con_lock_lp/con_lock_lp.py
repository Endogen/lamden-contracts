#  _   _      _           _         _      _____    _                _    
# | \ | |    | |         | |       | |    |  __ \  | |              | |   
# |  \| | ___| |__  _   _| | __ _  | |    | |__) | | |     ___   ___| | __
# | . ` |/ _ \ '_ \| | | | |/ _` | | |    |  ___/  | |    / _ \ / __| |/ /
# | |\  |  __/ |_) | |_| | | (_| | | |____| |      | |___| (_) | (__|   < 
# |_| \_|\___|_.__/ \__,_|_|\__,_| |______|_|      |______\___/ \___|_|\_\
#

I = importlib

lock_data = Hash(default_value="")

dex = Variable()
neb_base = Variable()
max_lock_time = Variable()

lock_fee = Variable()
lock_fee_discount = Variable()

OPERATORS = [
    'ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d',
    'e787ed5907742fa8d50b3ca2701ab8e03ec749ced806a15cdab800a127d7f863',
    '62783e94c14b0ae0c555f33ca6aa9699099606d636d4f0fd916bf912d8022045'
]
NEB_CONTRACT = 'con_nebula'
NEB_KEY_CONTRACT = 'con_neb_key001'
BURN_ADDRESS = 'neb_lock_lp_burn_address'

@construct
def seed():
    lock_fee.set(1)
    lock_fee_discount.set(0.1)

    max_lock_time.set(365)
    neb_base.set('con_neb_base_001')
    dex.set('con_rocketswap_official_v1_1')

@export
def lock_lp(lock_id: str, token_contract: str, lp_amount: float, lock_time_in_days: int):
    assert lp_amount > 0, "Negative LP amount not allowed!"
    assert lock_time_in_days > 0, "Negative lock time not allowed!"
    assert lock_time_in_days <= max_lock_time.get(), f"Max lock time is {max_lock_time.get()} days"
    assert lock_data[lock_id] == "", 'Lock ID already exists!'

    neb_key_balances = ForeignHash(foreign_contract=NEB_KEY_CONTRACT, foreign_name='balances')
    discount = lock_fee_discount.get() if neb_key_balances[ctx.caller] >= 1 else 0

    fee = lp_amount / 100 * (lock_fee.get() - discount)

    I.import_module(dex.get()).transfer_liquidity_from(
        contract=token_contract, 
        to=ctx.this, 
        main_account=ctx.caller, 
        amount=lp_amount)

    treasury = ForeignVariable(foreign_contract=NEB_CONTRACT, foreign_name='vault_contract')
    assert treasury.get(), 'Treasury contract not set!'

    I.import_module(dex.get()).transfer_liquidity(
        contract=token_contract, 
        to=treasury.get(), 
        amount=fee)

    lock_data[lock_id] = {
        "start_date": now, 
        "contract": token_contract, 
        "returned": False, 
        "amount": lp_amount - fee, 
        "owner": ctx.caller, 
        "days": lock_time_in_days, 
        "dex": dex.get(), 
    }
    
    return f'{lock_data[lock_id]["start_date"] + datetime.timedelta(days=lock_data[lock_id]["days"])}'

@export
def unlock_lp(lock_id: str):
    assert lock_data[lock_id] != "", "Unknown lock ID!"

    lock = lock_data[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"
    assert lock["returned"] == False, "Locked LP already returned!"

    lock_end = lock["start_date"] + datetime.timedelta(days=lock["days"])

    assert now > lock_end , f"Unlock date not reached: {lock_end}"

    I.import_module(lock["dex"]).transfer_liquidity(
        contract=lock["contract"], 
        to=lock["owner"], 
        amount=lock["amount"])

    lock["returned"] = True
    lock["return_date"] = now
    lock_data[lock_id] = lock

    return f'{lock["amount"]}'

@export
def extend_time(lock_id: str, days_to_extend: int):
    assert days_to_extend > 0, "Negative time extension not allowed!"
    assert lock_data[lock_id] != "", "Unknown lock ID!"

    lock = lock_data[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"
    assert lock["returned"] == False, "Locked LP already returned!"

    lock["days"] += days_to_extend

    error = f'Max lock time is {max_lock_time.get()} days. You try to set {lock["days"]} days'
    assert lock["days"] <= max_lock_time.get(), error

    lock_data[lock_id] = lock

    return f'{lock["start_date"] + datetime.timedelta(days=lock["days"])}'

@export
def extend_amount(lock_id: str, lp_amount: float):
    assert lp_amount > 0, "Negative LP amount not allowed!"
    assert lock_data[lock_id] != "", "Unknown lock ID!"

    lock = lock_data[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"
    assert lock["returned"] == False, "Locked LP already returned!"

    fee = lp_amount / 100 * lock_fee.get()

    I.import_module(dex.get()).transfer_liquidity_from(
        contract=lock["contract"], 
        to=ctx.this, 
        main_account=ctx.caller, 
        amount=lp_amount)

    treasury = ForeignVariable(foreign_contract=NEB_CONTRACT, foreign_name='vault_contract')

    assert treasury.get(), 'Treasury contract not set!'

    I.import_module(dex.get()).transfer_liquidity(
        contract=lock["contract"], 
        to=treasury.get(), 
        amount=fee)

    lock["amount"] += lp_amount - fee
    lock_data[lock_id] = lock

    return f'{lock["amount"]}'

@export
def lock_info(lock_id: str):
    assert lock_data[lock_id] != "", "Unknown lock ID!"

    lock = lock_data[lock_id]

    if lock["owner"] == BURN_ADDRESS:
        return f'{lock["amount"]} LP burned'
    if lock["returned"]:
        return f'LP returned on {lock["return_date"]}'
    else:
        return f'LP will unlock in {(lock["start_date"] + datetime.timedelta(days=lock["days"])) - now}'

@export
def burn_locked_lp(lock_id: str):
    assert lock_data[lock_id] != "", "Unknown lock ID!"

    lock = lock_data[lock_id]

    assert lock["owner"] == ctx.caller, "You are not the owner!"
    assert lock["returned"] == False, "Locked LP already returned!"

    I.import_module(dex.get()).transfer_liquidity(
        contract=lock["contract"], 
        to=BURN_ADDRESS, 
        amount=lock["amount"])

    lock["owner"] = BURN_ADDRESS
    lock_data[lock_id] = lock

    return f'{lock["amount"]}'

@export
def set_dex(dex_contract: str):
    dex.set(dex_contract)
    assert_owner()

@export
def set_neb_base(neb_base_contract: str):
    neb_base.set(neb_base_contract)
    assert_owner()

@export
def set_lock_fee(percent_of_lp: float):
    assert percent_of_lp >= 0, "Fee can not be negative!"
    lock_fee.set(percent_of_lp)
    assert_owner()

@export
def set_lock_fee_discount(percent_discount: float):
    assert percent_discount >= 0, "Fee discount can not be negative!"
    lock_fee_discount.set(percent_discount)
    assert_owner()

@export
def set_max_lock_time(max_time_in_days: float):
    assert max_time_in_days >= 1, "Max lock time can not be smaller than 1 day!"
    max_lock_time.set(max_time_in_days)
    assert_owner()

def assert_owner():
    assert ctx.caller in OPERATORS, 'Only executable by operators!'
