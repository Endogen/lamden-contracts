staking = Hash(default_value=0)

stake_con = Variable()
emission_con = Variable()

total_emission = Variable()
total_stake = Variable()

current_stake = Variable()
max_single_stake = Variable()

active = Variable()
funded = Variable()

creator_addr = Variable()
creator_lock = Variable()

start_date = Variable()
start_date_end = Variable()
end_date = Variable()

NEB_FEE = 2
OPERATORS = [
    'ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d',
    'e787ed5907742fa8d50b3ca2701ab8e03ec749ced806a15cdab800a127d7f863'
]

@export
def fund_vault(stake_contract: str, emission_contract: str, total_emission_amount: float, total_stake_amount: float,
               minutes_till_start: int, start_period_in_minutes: int, minutes_till_end: int, creator_lock_amount: float, max_single_stake_percent: float):
    
    assert funded.get() != True, 'Vault is already funded!'
    assert total_emission_amount > 0, 'total_emission_amount not valid!'
    assert total_stake_amount > 0, 'total_stake_amount not valid!'
    assert minutes_till_start > 0, 'minutes_till_start not valid!'
    assert start_period_in_minutes >= 2880, 'Staking needs to be open for at least 2 days!'
    assert minutes_till_end > 0, 'minutes_till_end not valid!'
    assert creator_lock_amount >= 0, 'dev_fee not valid!'
    assert max_single_stake_percent > 0, 'max_single_stake_percent not valid!'

    creator_addr.set(ctx.caller)
    creator_lock.set(creator_lock_amount)

    stake_con.set(stake_contract)
    emission_con.set(emission_contract)

    current_stake.set(0)
    total_emission.set(total_emission_amount)
    total_stake.set(total_stake_amount)
    max_single_stake.set(total_stake_amount / 100 * max_single_stake_percent)

    start_date.set(now + datetime.timedelta(minutes=minutes_till_start))
    start_date_end.set(start_date.get() + datetime.timedelta(minutes=start_period_in_minutes))
    end_date.set(start_date_end.get() + datetime.timedelta(minutes=minutes_till_end))

    vault = ForeignVariable(foreign_contract='con_nebula', foreign_name='vault_contract')

    if not vault.get():
        vault = Variable()
        vault.set('INTERNAL_NEB_VAULT')

    # Pay Nebula fee
    importlib.import_module(emission_con.get()).transfer_from(
        amount=total_emission.get() / 100 * NEB_FEE,
        main_account=ctx.caller,
        to=vault.get())

    # Lock creator tokens
    if creator_lock.get() > 0:
        send_to_vault(emission_con.get(), creator_lock.get())

    # Pay total emission amount
    send_to_vault(emission_con.get(), total_emission.get())

    active.set(True)
    funded.set(True)

@export
def send_to_vault(contract: str, amount: float):
    importlib.import_module(contract).transfer_from(
        main_account=ctx.caller,
        amount=amount,
        to=ctx.this)

@export
def stake(amount: float):
    assert_active()

    assert now > start_date.get(), f'Staking not started yet: {start_date.get()}'
    assert now < start_date_end.get(), f'Staking period ended: {start_date_end.get()}'
    assert amount > 0, 'Amount must be > 0'

    staking[ctx.caller] += amount
    send_to_vault(stake_con.get(), amount)
    current_stake.set(current_stake.get() + amount)

    assert staking[ctx.caller] <= max_single_stake.get(), f'Max user stake exceeded: {max_single_stake.get()}'
    assert current_stake.get() <= total_stake.get(), f'Max total stake exceeded: {total_stake.get()}'

@export
def unstake():
    assert_active()

    assert staking[ctx.caller] != 0, f'Address is not staking!'
    assert now > end_date.get(), f'End date not reached: {end_date.get()}'

    stake_percent = staking[ctx.caller] / current_stake.get() * 100
    user_emission = total_emission.get() / 100 * stake_percent

    # Pay emissions to user
    importlib.import_module(emission_con.get()).transfer(
        amount=user_emission,
        to=ctx.caller)

    # Pay stake to user
    importlib.import_module(stake_con.get()).transfer(
        amount=staking[ctx.caller],
        to=ctx.caller)

    staking[ctx.caller] = 0

    return f'Emission: {user_emission} {emission_con.get()}'

@export
def enable_vault():
    assert_owner()
    active.set(True)

@export
def disable_vault():
    assert_owner()
    active.set(False)

@export
def emergency_withdraw(contract: str, amount: float):
    assert_owner()
    importlib.import_module(contract).transfer(amount, ctx.caller)

@export
def pay_back_creator_fee():
    assert_active()

    assert now > end_date.get(), f'End date not reached: {end_date.get()}'
    assert creator_addr.get() == ctx.caller, 'You are not the vault creator!'
    assert creator_lock.get() > 0, 'No dev funds locked!'
    
    # Pay back locked fund to creator
    importlib.import_module(emission_con.get()).transfer(
        amount=creator_lock.get(),
        to=creator_addr.get())

def assert_active():
    assert active.get() == True, 'Vault inactive!'

def assert_owner():
    assert ctx.caller in OPERATORS, 'Only executable by operators!'