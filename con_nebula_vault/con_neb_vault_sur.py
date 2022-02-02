#  _   _      _           _          _____                  _                  __      __         _ _   
# | \ | |    | |         | |        / ____|                (_)                 \ \    / /        | | |  
# |  \| | ___| |__  _   _| | __ _  | (___  _   _ _ ____   _____   _____  _ __   \ \  / /_ _ _   _| | |_ 
# | . ` |/ _ \ '_ \| | | | |/ _` |  \___ \| | | | '__\ \ / / \ \ / / _ \| '__|   \ \/ / _` | | | | | __|
# | |\  |  __/ |_) | |_| | | (_| |  ____) | |_| | |   \ V /| |\ V / (_) | |       \  / (_| | |_| | | |_ 
# |_| \_|\___|_.__/ \__,_|_|\__,_| |_____/ \__,_|_|    \_/ |_| \_/ \___/|_|        \/ \__,_|\__,_|_|\__|
#

I = importlib

staking = Hash(default_value=0)
payouts = Hash(default_value=0)

start_date = Variable()
start_end_date = Variable()
end_date = Variable()

total_stake = Variable()
total_emission = Variable()
stake_contract = Variable()
active = Variable()

NEBULA_FEE = 5
EARLY_UNSTAKE_TAX = 5

OPERATORS = [
    'ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d',
    'e787ed5907742fa8d50b3ca2701ab8e03ec749ced806a15cdab800a127d7f863',
    '62783e94c14b0ae0c555f33ca6aa9699099606d636d4f0fd916bf912d8022045'
]

@export
def init(minutes_till_start: int, start_period_minutes: int, minutes_till_end: int, token_contract: str, seed_amount: float = 0):
    stake_contract.set(token_contract)
    
    total_emission.set(0)
    total_stake.set(0)

    start_date.set(now + datetime.timedelta(minutes=minutes_till_start))
    start_end_date.set(start_date.get() + datetime.timedelta(minutes=start_period_minutes))
    end_date.set(start_end_date.get() + datetime.timedelta(minutes=minutes_till_end))

    if seed_amount > 0:
        total_emission.set(seed_amount)

        I.import_module(stake_contract.get()).transfer_from(
            main_account=ctx.caller,
            amount=seed_amount,
            to=ctx.this)

    active.set(True)

@export
def active(is_active: bool):
    active.set(is_active)
    assert_owner()

@export
def stake(amount: float):
    assert_active()

    assert amount > 0, 'Negative amounts are not allowed'
    assert now > start_date.get(), f'Staking not started yet: {start_date.get()}'
    assert now < start_end_date.get(), f'Staking already ended: {start_end_date.get()}'

    I.import_module(stake_contract.get()).transfer_from(
        main_account=ctx.caller,
        amount=amount,
        to=ctx.this)

    staking[ctx.caller] += amount
    total_stake.set(total_stake.get() + amount)

@export
def unstake():
    assert_active()

    assert staking[ctx.caller] > 0, f'No stake found for this address'

    # You survived! Pay out stake + emissions
    if now > end_date.get():
        stake_percent = staking[ctx.caller] / total_stake.get() * 100
        user_emission = total_emission.get() / 100 * stake_percent

        payouts[ctx.caller] = staking[ctx.caller] + user_emission

        I.import_module(stake_contract.get()).transfer(
            amount=payouts[ctx.caller],
            to=ctx.caller)

    # No diamond hands? Pay out stake - early unstake tax
    else:
        tax = staking[ctx.caller] / 100 * EARLY_UNSTAKE_TAX
        total_emission.set(total_emission.get() + tax)

        payouts[ctx.caller] = staking[ctx.caller] - tax
        total_stake.set(total_stake.get() - staking[ctx.caller])

        I.import_module(stake_contract.get()).transfer(
            amount=payouts[ctx.caller],
            to=ctx.caller)

    staking[ctx.caller] = 0
    return f'{payouts[ctx.caller]}'

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