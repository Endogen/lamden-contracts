#  _   _      _           _         _      _____   __      __         _ _   
# | \ | |    | |         | |       | |    |  __ \  \ \    / /        | | |  
# |  \| | ___| |__  _   _| | __ _  | |    | |__) |  \ \  / /_ _ _   _| | |_ 
# | . ` |/ _ \ '_ \| | | | |/ _` | | |    |  ___/    \ \/ / _` | | | | | __|
# | |\  |  __/ |_) | |_| | | (_| | | |____| |         \  / (_| | |_| | | |_ 
# |_| \_|\___|_.__/ \__,_|_|\__,_| |______|_|          \/ \__,_|\__,_|_|\__|
#

I = importlib

staking = Hash(default_value=0)
locking = Hash(default_value=0)
levels = Hash(default_value=0)
con = Hash(default_value='')

trusted = Variable()
active = Variable()

VALIDATOR = '9a12554c2098567d22aaa9b787d73b606d2f2044a602186c3b9af65f6c58cfaf'

OPERATORS = [
    'ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d',
    'e787ed5907742fa8d50b3ca2701ab8e03ec749ced806a15cdab800a127d7f863'
]

@construct
def seed():
    con['neb'] = 'con_nebula'
    con['key'] = 'con_neb_key001'
    con['dex'] = 'con_rocketswap_official_v1_1'

    levels[1] = {'level': 1, 'lp': 0,     'key': 0, 'emission': 0.375}
    levels[2] = {'level': 2, 'lp': 18.75, 'key': 0, 'emission': 0.75}
    levels[3] = {'level': 3, 'lp': 0,     'key': 1, 'emission': 1}
    levels[4] = {'level': 4, 'lp': 37.5,  'key': 0, 'emission': 1.5}
    levels[5] = {'level': 5, 'lp': 75,    'key': 0, 'emission': 3}
    levels[6] = {'level': 6, 'lp': 150,   'key': 0, 'emission': 4}

    trusted.set([])
    active.set(True)

@export
def get_level(address: str):
    lp_stake = staking[address, 'lp']
    key_stake = staking[address, 'key']

    for i in range(10, 0, -1):
        if levels[i] == 0:
            continue
        
        level = levels[i]
        if (lp_stake >= level['lp']) and (key_stake >= level['key']):
            return level

    return levels[1]

@export
def show_level(address: str):
    l = get_level(address)
    return f'Level: {l["level"]}, LP: {l["lp"]}, KEY: {l["key"]}, Emission: {l["emission"]}'

@export
def stake(neb_lp_amount: float = 0, neb_key_amount: int = 0):
    assert_active()

    assert neb_lp_amount >= 0, 'Negative amounts are not allowed'
    assert neb_key_amount >= 0, 'Negative amounts are not allowed'

    if neb_lp_amount > 0:
        staking['lp'] += neb_lp_amount
        staking[ctx.caller, 'lp'] += neb_lp_amount

        I.import_module(con['dex']).transfer_liquidity_from(
            contract=con['neb'],
            to=ctx.this, 
            main_account=ctx.caller, 
            amount=neb_lp_amount)   
    
    if neb_key_amount > 0:
        staking['key'] += neb_key_amount
        staking[ctx.caller, 'key'] += neb_key_amount

        I.import_module(con['key']).transfer_from(
            main_account=ctx.caller,
            amount=neb_key_amount,
            to=ctx.this)

@export
def unstake(neb_lp_amount: float = 0, neb_key_amount: int = 0):
    assert_active()

    assert neb_lp_amount >= 0, 'Negative amounts are not allowed'
    assert neb_key_amount >= 0, 'Negative amounts are not allowed'

    staked_lp = staking[ctx.caller, 'lp']
    staked_key = staking[ctx.caller, 'key']

    highest_lp = 0
    highest_key = 0

    if isinstance(locking[ctx.caller], list):
        for lock_contract in locking[ctx.caller]:
            locked_lp = locking[ctx.caller, lock_contract, 'lp']
            locked_key = locking[ctx.caller, lock_contract, 'key']

            if locked_lp > highest_lp: highest_lp = locked_lp
            if locked_key > highest_key: highest_key = locked_key

    lp_available = staked_lp - highest_lp
    key_available = staked_key - highest_key

    assert lp_available >= neb_lp_amount, f'Only {lp_available} NEB LP available to unstake'
    assert key_available >= neb_key_amount, f'Only {key_available} NEB KEY available to unstake'

    if neb_lp_amount > 0:
        I.import_module(con['dex']).transfer_liquidity(
            contract=con['neb'],
            to=ctx.caller, 
            amount=neb_lp_amount)

    if neb_key_amount > 0:
        I.import_module(con['key']).transfer(
            amount=neb_key_amount,
            to=ctx.caller)

    staking[ctx.caller, 'lp'] -= neb_lp_amount
    staking[ctx.caller, 'key'] -= neb_key_amount

    staking['lp'] -= neb_lp_amount
    staking['key'] -= neb_key_amount

@export
def lock():
    user_address = ctx.signer
    vault_contract = ctx.caller

    assert vault_contract in trusted.get(), f'Unknown contract {vault_contract}'

    if not isinstance(locking[user_address], list):
        locking[user_address] = []

    lock_list = locking[user_address]

    if not vault_contract in lock_list:
        lock_list.append(vault_contract)

    locking[user_address] = lock_list

    level = get_level(user_address)

    locking[user_address, vault_contract, 'lp'] = level['lp']
    locking[user_address, vault_contract, 'key'] = level['key']

    return level

@export
def unlock():
    user_address = ctx.signer
    vault_contract = ctx.caller

    assert vault_contract in trusted.get(), f'Unknown contract {vault_contract}'

    lock_list = locking[user_address]
    
    if vault_contract in lock_list:
        lock_list.remove(vault_contract)
    
    locking[user_address] = lock_list

    locking[user_address, vault_contract, 'lp'] = 0
    locking[user_address, vault_contract, 'key'] = 0

@export
def set_contract(key: str, value: str):
    con[key] = value
    assert_owner()

@export
def set_levels(level: int, data: dict):
    levels[level] = data
    assert_owner()

@export
def add_valid_vault(contract_name: str):
    assert ctx.caller == VALIDATOR, 'Only validator can add trusted contracts!'
    
    trusted_contracts = trusted.get()
    if contract_name not in trusted_contracts:
        trusted_contracts.append(contract_name)
        trusted.set(trusted_contracts)

@export
def remove_valid_vault(contract_name: str):
    assert ctx.caller == VALIDATOR, 'Only validator can remove trusted contracts!'
    
    trusted_contracts = trusted.get()
    if contract_name in trusted_contracts:
        trusted_contracts.remove(contract_name)
        trusted.set(trusted_contracts)

@export
def emergency_lock(user_address: str, vault_contract: str, lp_amount: float, key_amount: float):
    assert_owner()

    if not isinstance(locking[user_address], list):
        locking[user_address] = []

    lock_list = locking[user_address]

    if not vault_contract in lock_list:
        lock_list.append(vault_contract)

    locking[user_address] = lock_list

    locking[user_address, vault_contract, 'lp'] = lp_amount
    locking[user_address, vault_contract, 'key'] = key_amount

@export
def emergency_unlock(user_address: str, vault_contract: str):
    assert_owner()

    lock_list = locking[user_address]
    
    if vault_contract in lock_list:
        lock_list.remove(vault_contract)
    
    locking[user_address] = lock_list

    locking[user_address, vault_contract, 'lp'] = 0
    locking[user_address, vault_contract, 'key'] = 0

@export
def emergency_withdraw_token(contract_name: str, amount: float):
    I.import_module(contract_name).transfer(amount, ctx.caller)
    assert_owner()

@export
def emergency_withdraw_lp(contract_name: str, amount: float):
    I.import_module(con['dex']).transfer_liquidity(contract_name, ctx.caller, amount)
    assert_owner()

@export
def active(is_active: bool):
    active.set(is_active)
    assert_owner()

def assert_active():
    assert active.get() == True, 'Vault inactive!'

def assert_owner():
    assert ctx.caller in OPERATORS, 'Only executable by operators!'
