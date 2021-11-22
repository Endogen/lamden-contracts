I = importlib

staking = Hash(default_value=0)
locking = Hash(default_value=0)
levels = Hash(default_value=0)
con = Hash(default_value='')

active = Variable()

OPERATORS = [
    'ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d',
    'e787ed5907742fa8d50b3ca2701ab8e03ec749ced806a15cdab800a127d7f863'
]

@construct
def seed():
    con['neb'] = 'con_nebula'
    con['key'] = 'con_neb_key001'
    con['prx'] = 'con_neb_vault_proxy_001'
    con['dex'] = 'con_rocketswap_official_v1_1'

    levels[1] = {'level': 1, 'lp': 0,     'key': 0, 'emission': 0.375}
    levels[2] = {'level': 2, 'lp': 18.75, 'key': 0, 'emission': 0.75}
    levels[3] = {'level': 3, 'lp': 0,     'key': 1, 'emission': 1}
    levels[4] = {'level': 4, 'lp': 37.5,  'key': 0, 'emission': 1.5}
    levels[5] = {'level': 5, 'lp': 75,    'key': 0, 'emission': 3}
    levels[6] = {'level': 6, 'lp': 150,   'key': 0, 'emission': 4}

    active.set(True)

@export
def get_level(address: str):
    lp_stake = staking[address, 'lp']
    key_stake = staking[address, 'key']

    return get_level_from_amount(lp_stake, key_stake)

@export
def get_level_from_amount(lp_amount: float, key_amount: int):
    for i in range(10, 0, -1):
        if levels[i] == 0:
            continue
        
        level = levels[i]
        if (lp_amount >= level['lp']) and (key_amount >= level['key']):
            return level

    return levels[1]

@export
def show_level(address: str):
    l = get_level(address)
    return f'Level: {l["level"]}, LP: {l["lp"]}, KEY: {l["key"]}, Emission: {l["emission"]}'

@export
def stake(neb_lp_amount: float = 0, neb_key_amount: int = 0):
    assert_active()

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

    staked_lp = staking[ctx.caller, 'lp']
    staked_key = staking[ctx.caller, 'key']

    current_level = get_level_from_amount(staked_lp, staked_key)['level']
    highest_level = 1

    if isinstance(locking[ctx.caller], list):
        for lock_contract in locking[ctx.caller]:
            locked_level = locking[ctx.caller, lock_contract, 'level']

            if locked_level > highest_level:
                highest_level = locked_level

    locked_lp = levels[highest_level]['lp']
    locked_key = levels[highest_level]['key']

    lp_available = staked_lp - locked_lp
    key_available = staked_key - locked_key

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
    trusted = ForeignVariable(foreign_contract=con['prx'], foreign_name='contracts')
    assert ctx.caller in trusted.get(), f'Unknown contract {ctx.caller}'

    if not isinstance(locking[ctx.signer], list):
        locking[ctx.signer] = []        

    lock_list = locking[ctx.signer]

    if not ctx.caller in lock_list:
        lock_list.append(ctx.caller)

    locking[ctx.signer] = lock_list

    level = get_level(ctx.signer)

    locking[ctx.signer, ctx.caller, 'level'] = level['level']

    return level

@export
def unlock():
    trusted = ForeignVariable(foreign_contract=con['prx'], foreign_name='contracts')
    assert ctx.caller in trusted.get(), f'Unknown contract {ctx.caller}'

    lock_list = locking[ctx.signer]
    
    if ctx.caller in lock_list:
        lock_list.remove(ctx.caller)
    
    locking[ctx.signer] = lock_list
    locking.clear(ctx.signer, ctx.caller)

@export
def set_contract(key: str, value: str):
    con[key] = value
    assert_owner()

@export
def set_levels(level: int, data: dict):
    levels[level] = data
    assert_owner()

@export
def emergency_withdraw_token(contract_name: str, amount: float):
    I.import_module(contract_name).transfer(amount, ctx.caller)
    assert_owner()

@export
def emergency_withdraw_lp(contract_name: str, amount: float):
    I.import_module(con['dex']).transfer_liquidity(contract_name, ctx.caller, amount)
    assert_owner()

@export
def enable_vault():
    active.set(True)
    assert_owner()

@export
def disable_vault():
    active.set(False)
    assert_owner()

def assert_active():
    assert active.get() == True, 'Vault inactive!'

def assert_owner():
    assert ctx.caller in OPERATORS, 'Only executable by operators!'
