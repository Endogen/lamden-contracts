#  _   _      _           _         ______      _                        _  __      __         _ _   
# | \ | |    | |         | |       |  ____|    | |                      | | \ \    / /        | | |  
# |  \| | ___| |__  _   _| | __ _  | |__  __  _| |_ ___ _ __ _ __   __ _| |  \ \  / /_ _ _   _| | |_ 
# | . ` |/ _ \ '_ \| | | | |/ _` | |  __| \ \/ / __/ _ \ '__| '_ \ / _` | |   \ \/ / _` | | | | | __|
# | |\  |  __/ |_) | |_| | | (_| | | |____ >  <| ||  __/ |  | | | | (_| | |    \  / (_| | |_| | | |_ 
# |_| \_|\___|_.__/ \__,_|_|\__,_| |______/_/\_\\__\___|_|  |_| |_|\__,_|_|     \/ \__,_|\__,_|_|\__|
#
# Version 1.4

I = importlib

staking = Hash(default_value=0)
payouts = Hash(default_value=0)

stake_con = Variable()
emission_con = Variable()

total_emission = Variable()
total_stake = Variable()

current_stake = Variable()
max_single_stake = Variable()

creator_addr = Variable()
creator_lock = Variable()

start_date = Variable()
start_date_end = Variable()
end_date = Variable()

funded = Variable()

NEB_FEE = 2
NEB_FEE_DISCOUNT = 0.2
NEB_INSTANT_FEE = 5000

NEB_CONTRACT = 'con_nebula'
NEB_KEY_CONTRACT = 'con_neb_key001'

MIN_START_TIME = 5
MAX_START_TIME = 10080

MIN_STAKE_TIME = 1440
MAX_STAKE_TIME = 10080

MIN_LOCK_TIME = 1440
MAX_LOCK_TIME = 518400

@export
def fund_vault(stake_contract: str, total_stake_amount: float, emission_contract: str, total_emission_amount: float, 
               minutes_till_start: int, start_period_in_minutes: int, minutes_till_end: int, 
               max_single_stake_percent: float, creator_lock_amount: float = 0):
    
    assert funded.get() != True, 'Vault is already funded!'

    assert total_stake_amount > 0, 'Total stake amount must be > 0'
    assert total_emission_amount > 0, 'Total emission amount must be > 0'
    
    assert creator_lock_amount >= 0, 'Creator lock amount must be >= 0'
    
    assert max_single_stake_percent > 0, 'Maximum single stake percent must be > 0'
    assert max_single_stake_percent < 100, 'Maximum single stake percent must be < 100'
    
    assert minutes_till_start >= MIN_START_TIME, f'Minimum time from vault start to staking start: {MIN_START_TIME} minutes'
    assert minutes_till_start <= MAX_START_TIME, f'Maximum time from vault start to staking start: {MAX_START_TIME} minutes'
    
    assert start_period_in_minutes >= MIN_STAKE_TIME, f'Minimum time from staking start to staking end: {MIN_STAKE_TIME / 60} hours'
    assert start_period_in_minutes <= MAX_STAKE_TIME, f'Maximum time from staking start to staking end: {MAX_STAKE_TIME / 60 / 24} days'

    assert minutes_till_end >= MIN_LOCK_TIME, f'Minimum time from staking end to vault end: {MIN_LOCK_TIME / 60} hours'
    assert minutes_till_end <= MAX_LOCK_TIME, f'Maximum time from staking end to vault end: {MAX_LOCK_TIME / 60 / 24} days'

    sc = I.import_module(stake_contract)
    ec = I.import_module(emission_contract)

    stake_con.set(stake_contract)
    emission_con.set(emission_contract)

    creator_addr.set(ctx.caller)
    creator_lock.set(creator_lock_amount)

    current_stake.set(0)
    total_stake.set(total_stake_amount)
    total_emission.set(total_emission_amount)
    max_single_stake.set(total_stake_amount / 100 * max_single_stake_percent)

    start_date.set(now + datetime.timedelta(minutes=minutes_till_start))
    start_date_end.set(start_date.get() + datetime.timedelta(minutes=start_period_in_minutes))
    end_date.set(start_date_end.get() + datetime.timedelta(minutes=minutes_till_end))

    neb_key_balances = ForeignHash(foreign_contract=NEB_KEY_CONTRACT, foreign_name='balances')

    if neb_key_balances[ctx.caller] and neb_key_balances[ctx.caller] >= 1:
        discount = NEB_FEE_DISCOUNT
    else:
        discount = 0

    fee = total_emission.get() / 100 * (NEB_FEE - discount)
    total_amount = total_emission.get() + fee + creator_lock.get()

    send_to_vault(emission_con.get(), total_amount)

    treasury = ForeignVariable(foreign_contract=NEB_CONTRACT, foreign_name='vault_contract')
    assert treasury.get(), 'Treasury contract not set!'

    I.import_module(emission_con.get()).transfer(
        to=treasury.get(),
        amount=fee)

    I.import_module(NEB_CONTRACT).transfer_from(
        main_account=ctx.caller,
        amount=NEB_INSTANT_FEE,
        to='NEBULA_BURN_ADDRESS')

    funded.set(True)

def send_to_vault(contract: str, amount: float):
    I.import_module(contract).transfer_from(
        main_account=ctx.caller,
        amount=amount,
        to=ctx.this)

@export
def stake(amount: float):
    assert amount > 0, 'Negative amounts are not allowed'
    assert now > start_date.get(), f'Staking not started yet: {start_date.get()}'
    assert now < start_date_end.get(), f'Staking period ended: {start_date_end.get()}'

    staking[ctx.caller] += amount
    send_to_vault(stake_con.get(), amount)
    current_stake.set(current_stake.get() + amount)

    assert staking[ctx.caller] <= max_single_stake.get(), f'Max user stake exceeded: {max_single_stake.get()}'
    assert current_stake.get() <= total_stake.get(), f'Max total stake exceeded: {total_stake.get()}'

@export
def unstake():
    assert staking[ctx.caller] != 0, f'Address is not staking!'
    assert now > end_date.get(), f'End date not reached: {end_date.get()}'

    stake_percent = staking[ctx.caller] / current_stake.get() * 100
    user_emission = total_emission.get() / 100 * stake_percent

    I.import_module(emission_con.get()).transfer(
        amount=user_emission,
        to=ctx.caller)

    I.import_module(stake_con.get()).transfer(
        amount=staking[ctx.caller],
        to=ctx.caller)

    staking[ctx.caller] = 0
    payouts[ctx.caller] = user_emission

    return f'Emission: {user_emission} {emission_con.get()}'

@export
def payout_only_stake(amount: float):
    assert staking[ctx.caller] != 0, f'Address is not staking!'
    assert now > end_date.get(), f'End date not reached: {end_date.get()}'
    assert amount <= staking[ctx.caller], f'Max unstake amount is {staking[ctx.caller]}'

    I.import_module(stake_con.get()).transfer(
        amount=amount,
        to=ctx.caller)

    current_stake.set(current_stake.get() - amount)

    staking[ctx.caller] -= amount
    payouts[ctx.caller] = 0

    return f'Remaining Stake: {staking[ctx.caller]} {stake_con.get()}'

@export
def pay_back_locked_creator_tokens(pay_to_address: str):
    assert now > end_date.get(), f'End date not reached: {end_date.get()}'
    assert creator_addr.get() == ctx.caller, 'You are not the vault creator!'
    assert creator_lock.get() > 0, 'No creator funds locked!'

    I.import_module(emission_con.get()).transfer(
        amount=creator_lock.get(),
        to=pay_to_address)
