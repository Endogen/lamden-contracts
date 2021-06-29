import currency as tau
import con_degen as degen

random.seed()

owner = Variable()
min_amount = Variable()
max_amount = Variable()
multiplier = Variable()
degen_payout = Variable()
degen_balance = Variable()

@construct
def init():
    owner.set(ctx.caller)
    min_amount.set(10)
    max_amount.set(100)
    multiplier.set(5)
    degen_payout.set(0.5)
    degen_balance.set(0)

@export
def roll(guess: int, amount: float):
    error = "Not a valid dice number"
    assert (guess >= 1 and guess <= 6), error

    error = "Min bet amount is " + str(min_amount.get())
    assert amount >= min_amount.get(), error

    error = "Max bet amount is " + str(max_amount.get())
    assert amount <= max_amount.get(), error

    balance = tau.balance_of(account=ctx.this)

    error = "Contract balance too low to pay for possible win"
    assert balance >= amount * multiplier.get(), error

    tau.transfer_from(
        amount=amount, 
        to=ctx.this, 
        main_account=ctx.caller)

    result = random.randint(1, 6)

    if result == guess:
        tau.transfer(
            amount=amount * multiplier.get(), 
            to=ctx.caller)
    else:
        degen_amount = degen_payout.get() * amount

        if degen_balance.get() >= degen_amount:
            degen.transfer(
                amount=degen_amount, 
                to=ctx.caller)

            degen_balance.set(degen_balance.get() - degen_amount)

    return result

@export
def deposit_tau(amount: float):
    tau.transfer_from(
        amount=amount, 
        to=ctx.this, 
        main_account=ctx.caller)                                        

@export
def withdraw_tau(amount: float):
    error = "Only the owner can request a payout"
    assert owner.get() == ctx.caller, error

    tau.transfer(
        amount=amount, 
        to=ctx.caller)

@export
def deposit_degen(amount: float):
    degen.transfer_from(
        amount=amount, 
        to=ctx.this, 
        main_account=ctx.caller)

    degen_balance.set(degen_balance.get() + amount)

@export
def withdraw_degen(amount: float):
    error = "Only the owner can withdraw DEGEN tokens"
    assert owner.get() == ctx.caller, error

    degen.transfer(
        amount=amount, 
        to=ctx.caller)

    degen_balance.set(degen_balance.get() - amount)

@export
def set_min(amount: int):
    error = "Only the owner can adjust the min amount"
    assert owner.get() == ctx.caller, error

    min_amount.set(amount)

@export
def set_max(amount: int):
    error = "Only the owner can adjust the max amount"
    assert owner.get() == ctx.caller, error

    max_amount.set(amount)

@export
def set_loss_payout(amount: float):
    error = "Only the owner can adjust the loss payout"
    assert owner.get() == ctx.caller, error

    degen_payout.set(amount)
