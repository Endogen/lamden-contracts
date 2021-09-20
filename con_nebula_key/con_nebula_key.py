# 888b    888          888               888              888    d8P  8888888888 Y88b   d88P 
# 8888b   888          888               888              888   d8P   888         Y88b d88P  
# 88888b  888          888               888              888  d8P    888          Y88o88P   
# 888Y88b 888  .d88b.  88888b.  888  888 888  8888b.      888d88K     8888888       Y888P    
# 888 Y88b888 d8P  Y8b 888 "88b 888  888 888     "88b     8888888b    888            888     
# 888  Y88888 88888888 888  888 888  888 888 .d888888     888  Y88b   888            888     
# 888   Y8888 Y8b.     888 d88P Y88b 888 888 888  888     888   Y88b  888            888     
# 888    Y888  "Y8888  88888P"   "Y88888 888 "Y888888     888    Y88b 8888888888     888     


import con_nebula as neb

staking = Hash(default_value='')
balances = Hash(default_value=0)
metadata = Hash()

active = Variable()
total_supply = Variable()

stake_tax = Variable()
stake_amount = Variable()
stake_start_date = Variable()
stake_start_period = Variable()
stake_period = Variable()

OPERATORS = [
    'ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d',
    'e787ed5907742fa8d50b3ca2701ab8e03ec749ced806a15cdab800a127d7f863'
]

@construct
def seed():
    metadata['token_name'] = "Nebula KEY"
    metadata['token_symbol'] = "KEY"
    metadata['operator'] = ctx.caller

    stake_tax.set(1)
    stake_amount.set(1_000_000)
    stake_start_date.set(now)
    stake_start_period.set(4)
    stake_period.set(21)

    active.set(False)
    total_supply.set(0)

@export
def change_metadata(key: str, value: Any):
    assert_owner()

    metadata[key] = value

@export
def transfer(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'
    assert balances[ctx.caller] >= amount, 'Not enough coins to send!'
    assert is_int(amount), 'Amount must be an Integer!'

    balances[ctx.caller] -= amount
    balances[to] += amount

@export
def approve(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'
    assert is_int(amount), 'Amount must be an Integer!'

    balances[ctx.caller, to] += amount

@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, 'Cannot send negative balances!'
    assert balances[main_account, ctx.caller] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'\
        .format(balances[main_account, ctx.caller], amount)
    assert balances[main_account] >= amount, 'Not enough coins to send!'
    assert is_int(amount), 'Amount must be an Integer!'

    balances[main_account, ctx.caller] -= amount
    balances[main_account] -= amount
    balances[to] += amount

def is_int(amount: float):
    int_amount = int(amount)
    return int_amount == amount

@export
def stake():
    assert active.get() == True, 'Contract inactive!'
    assert staking[ctx.caller] == '', 'Address is already staking!'
    assert now < (stake_start_date.get() + datetime.timedelta(days=stake_start_period.get())), 'Staking start period ended!'

    neb.transfer_from(amount=stake_amount.get(), to=ctx.this, main_account=ctx.caller)

    staking[ctx.caller] = str(now)

@export
def unstake():
    assert active.get() == True, 'Contract inactive!'
    assert staking[ctx.caller] != '', 'Address is not staking!'

    total_stake_time = stake_start_period.get() + stake_period.get()

    if now < (stake_start_date.get() + datetime.timedelta(days=total_stake_time)):
        # Calculate early unstake tax and payout amount
        tax = int(stake_amount.get() / 100 * stake_tax.get())
        payout = stake_amount.get() - tax

        # Pay NEB back to user (minus tax for early unstake)
        neb.transfer(amount=payout, to=ctx.caller)

        # Retrieve vault contract
        vault = ForeignVariable(foreign_contract='con_nebula', foreign_name='vault_contract')

        # If no vault contract set, use internal vault
        if not vault.get():
            vault = Variable()
            vault.set('INTERNAL_NEB_VAULT')

        # Pay tax to vault
        neb.transfer(amount=tax, to=vault.get())

        # Reset staking date
        staking[ctx.caller] = ''

        return 'Unstaked early. No KEY token minted. Paid back {} NEB'.format(int(payout))

    else:
        # Pay NEB back to user
        neb.transfer(amount=stake_amount.get(), to=ctx.caller)

        # Mint KEY token for user
        balances[ctx.caller] += 1

        # Add newly minted KEY to total supply
        total_supply.set(total_supply.get() + 1)

        # Reset staking date
        staking[ctx.caller] = ''

        return 'Unstaked and minted 1 KEY token. Paid back {} NEB'.format(int(stake_amount.get()))

@export
def start():
    assert_owner()
    staking.clear()
    stake_start_date.set(now)

@export
def set_stake_start_period(days: int):
    assert_owner()
    stake_start_period.set(days)

@export
def set_stake_period(days: int):
    assert_owner()
    stake_period.set(days)

@export
def set_stake_amount(amount: float):
    assert_owner()
    assert amount > 0, 'Cannot set negative amount!'
    stake_amount.set(amount)

@export
def set_stake_tax(percent: float):
    assert_owner()
    assert percent > 0 and percent < 100, 'Wrong tax value!'
    stake_tax.set(percent)

@export
def time_until_unstake():
    assert staking[ctx.caller] != '', 'Address is not staking!'
    total_stake_time = stake_start_period.get() + stake_period.get()
    return (stake_start_date.get() - now) + datetime.timedelta(days=total_stake_time)

@export
def enable():
    assert_owner()
    active.set(True)

@export
def disable():
    assert_owner()
    active.set(False)

@export
def emergency_withdraw(amount: float):
    assert_owner()
    neb.transfer(amount, ctx.caller)

@export
def total_supply():
    return int(total_supply.get())

def assert_owner():
    assert ctx.caller in OPERATORS, 'Only executable by operators!'
 