#  _   _      _           _         _____       _                        _  __      __         _ _   
# | \ | |    | |         | |       |_   _|     | |                      | | \ \    / /        | | |  
# |  \| | ___| |__  _   _| | __ _    | |  _ __ | |_ ___ _ __ _ __   __ _| |  \ \  / /_ _ _   _| | |_ 
# | . ` |/ _ \ '_ \| | | | |/ _` |   | | | '_ \| __/ _ \ '__| '_ \ / _` | |   \ \/ / _` | | | | | __|
# | |\  |  __/ |_) | |_| | | (_| |  _| |_| | | | ||  __/ |  | | | | (_| | |    \  / (_| | |_| | | |_ 
# |_| \_|\___|_.__/ \__,_|_|\__,_| |_____|_| |_|\__\___|_|  |_| |_|\__,_|_|     \/ \__,_|\__,_|_|\__|
#

I = importlib

staking = Hash(default_value=0)
payouts = Hash(default_value=0)

emission_con = Variable()
total_emission = Variable()

total_stake = Variable()
current_stake = Variable()

active = Variable()
funded = Variable()

start_date = Variable() 
start_date_end = Variable()
end_date = Variable()

NEB_FEE = 2
NEB_CONTRACT = 'con_nebula'
LP_VAULT = 'con_neb_vault_lp_005'
MIN_STAKE_PERIOD = 2880
MAX_RUNTIME = 129600

OPERATORS = [
    'ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d',
    'e787ed5907742fa8d50b3ca2701ab8e03ec749ced806a15cdab800a127d7f863'
]

@export
def fund_vault(emission_contract: str, total_emission_amount: float, total_stake_amount: float,
               minutes_till_start: int, start_period_in_minutes: int, minutes_till_end: int):
    
    assert funded.get() != True, 'Vault is already funded!'
    assert total_emission_amount > 0, 'total_emission_amount not valid!'
    assert total_stake_amount > 0, 'total_stake_amount not valid!'
    assert minutes_till_start > 0, 'minutes_till_start not valid!'
    assert start_period_in_minutes >= MIN_STAKE_PERIOD, 'Staking needs to be open for at least 2 days!'
    assert minutes_till_end > 0 and minutes_till_end <= MAX_RUNTIME, 'minutes_till_end not valid!'

    emission_con.set(emission_contract)

    current_stake.set(0)
    total_emission.set(total_emission_amount)
    total_stake.set(total_stake_amount)

    start_date.set(now + datetime.timedelta(minutes=minutes_till_start))
    start_date_end.set(start_date.get() + datetime.timedelta(minutes=start_period_in_minutes))
    end_date.set(start_date_end.get() + datetime.timedelta(minutes=minutes_till_end))

    single_fee = (total_emission.get() / 100 * NEB_FEE) / len(OPERATORS)

    for address in OPERATORS:
        I.import_module(emission_con.get()).transfer_from(
            main_account=ctx.caller,
            amount=single_fee,
            to=address)

    send_to_vault(emission_con.get(), total_emission.get())

    active.set(True)
    funded.set(True)

@export
def send_to_vault(contract: str, amount: float):
    I.import_module(contract).transfer_from(
        main_account=ctx.caller,
        amount=amount,
        to=ctx.this)

@export
def stake(neb_amount: float):
    assert_active()

    assert neb_amount > 0, 'Negative amounts are not allowed'
    assert now > start_date.get(), f'Staking not started yet: {start_date.get()}'
    assert now < start_date_end.get(), f'Staking period ended: {start_date_end.get()}'

    staking[ctx.caller] += neb_amount
    send_to_vault(NEB_CONTRACT, neb_amount)
    current_stake.set(current_stake.get() + neb_amount)

    level = I.import_module(LP_VAULT).lock()

    max_stake = total_stake.get() / 100 * level['emission']

    assert staking[ctx.caller] <= max_stake, f'Max stake exceeded: {max_stake} NEB (Level {level["level"]})'
    assert current_stake.get() <= total_stake.get(), f'Max total stake exceeded: {total_stake.get()} NEB'

@export
def unstake():
    assert_active()

    assert staking[ctx.caller] != 0, f'Address is not staking!'
    assert now > end_date.get(), f'End date not reached: {end_date.get()}'

    stake_percent = staking[ctx.caller] / current_stake.get() * 100
    user_emission = total_emission.get() / 100 * stake_percent

    I.import_module(emission_con.get()).transfer(
        amount=user_emission,
        to=ctx.caller)

    I.import_module(NEB_CONTRACT).transfer(
        amount=staking[ctx.caller],
        to=ctx.caller)

    I.import_module(LP_VAULT).unlock()

    staking[ctx.caller] = 0
    payouts[ctx.caller] = user_emission

    return f'Emission: {user_emission} {emission_con.get()}'

@export
def active(is_active: bool):
    active.set(is_active)
    assert_owner()

@export
def emergency_withdraw(contract: str, amount: float):
    I.import_module(contract).transfer(amount, ctx.caller)
    assert_owner()

@export
def emergency_set_stake(address: str, amount: float):
    staking[address] = amount
    assert_owner()

def assert_active():
    assert active.get() == True, 'Vault inactive!'

def assert_owner():
    assert ctx.caller in OPERATORS, 'Only executable by operators!'