import con_mintorburn as mob

random.seed()

owner = Variable()

min_amount = Variable()
max_amount = Variable()
multiplier = Variable()

@construct
def seed():
    owner.set('ff61544ea94eaaeb5df08ed863c4a938e9129aba6ceee5f31b6681bdede11b89')
    min_amount.set(50_000)
    max_amount.set(1_000_000)
    multiplier.set(5)

@export
def roll(guess: int, amount: float):
    error = 'Not a valid dice number'
    assert guess >= 1 and guess <= 6, error
    error = 'Min bet amount is ' + str(min_amount.get()) + ' MOB'
    assert amount >= min_amount.get(), error
    error = 'Max bet amount is ' + str(max_amount.get()) + ' MOB'
    assert amount <= max_amount.get(), error
    
    balance = mob.balance_of(address=ctx.this)
    
    error = 'MOB balance of contract too low to pay for possible win'
    assert balance >= amount * multiplier.get(), error
    
    mob.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)
    
    result = random.randint(1, 6)
    
    if result == guess:
        mob.transfer(amount=amount * multiplier.get(), to=ctx.caller)
    
    return result

@export
def pay_in(amount: float):
    mob.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)

@export
def pay_out(amount: float):
    error = 'Only the owner can request a payout'
    assert owner.get() == ctx.caller, error
    mob.transfer(amount=amount, to=ctx.caller)

@export
def set_min(amount: int):
    error = 'Only the owner can adjust the min amount'
    assert owner.get() == ctx.caller, error
    min_amount.set(amount)

@export
def set_max(amount: int):
    error = 'Only the owner can adjust the max amount'
    assert owner.get() == ctx.caller, error
    max_amount.set(amount)
