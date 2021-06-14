import currency

random.seed()

owner = Variable()
min_amount = Variable()
max_amount = Variable()
multiplier = Variable()

def ():
    owner.set(ctx.caller)
    min_amount.set(10)
    max_amount.set(50)
    multiplier.set(5)

@export()
def roll(guess: int, amount: float):
    error = 'Not a valid dice number'
    assert guess >= 1 and guess <= 6, error

    error = 'Min bet amount is ' + str(min_amount.get())
    assert amount >= min_amount.get(), error

    error = 'Max bet amount is ' + str(max_amount.get())
    assert amount <= max_amount.get(), error

    balance = currency.balance_of(account=ctx.this)

    error = 'Contract balance too low to pay for possible win'
    assert balance >= amount * multiplier.get(), error

    currency.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)

    result = random.randint(1, 6)

    if result == guess:
        currency.transfer(amount=amount * multiplier.get(), to=ctx.caller)

    return result

@export()
def pay_in(amount: float):
    currency.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)

@export()
def pay_out(amount: float):
    error = 'Only the owner can request a payout'
    assert owner.get() == ctx.caller, error

    currency.transfer(amount=amount, to=ctx.caller)

@export()
def adjust_min(amount: int):
    error = 'Only the owner can adjust the min amount'
    assert owner.get() == ctx.caller, error

    min_amount.set(amount)

@export()
def adjust_max(amount: int):
    error = 'Only the owner can adjust the max amount'
    assert owner.get() == ctx.caller, error

    max_amount.set(amount)