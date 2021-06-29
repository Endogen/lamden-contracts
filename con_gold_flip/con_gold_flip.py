random.seed()
I = importlib

owner = Variable()
burn_rate = Variable()
reserve_rate = Variable()
min_amount = Variable()
max_amount = Variable()
burn_address = Variable()
reserve_address = Variable()

@construct
def init():
    # Owner of this contract
    owner.set(ctx.caller)
    # Burn rate for lost flips in %
    burn_rate.set(1.0)
    # Reserve rate for lost flips in %
    reserve_rate.set(1.5)
    # Min amount of tokens to bet
    min_amount.set(2500000)
    # Max amount of tokens to bet
    max_amount.set(10000000)
    # Sending to this address will burn tokens
    burn_address.set("0000000000000BURN0000000000000")
    # Sending to this address will add tokens to reserve
    reserve_address.set("96dae3b6213fb80eac7c6f4fa0fd26f34022741c56773107b20199cb43f5ed62")


@export
def flip(amount: float, token_contract: str):
    error = "Amount must be equal to or greater than " + str(min_amount.get())
    assert amount >= min_amount.get(), error

    error = "Amount must be equal to or less than " + str(max_amount.get())
    assert amount <= max_amount.get(), error

    # Transfer tokens from user to contract
    I.import_module(token_contract).transfer_from(
        amount=amount,
        to=ctx.this,
        main_account=ctx.caller)

    # Randomly decide if user won or lost
    if random.choice([True, False]):
        # Transfer tokens from contract to user
        I.import_module(token_contract).transfer(
            amount=amount * 2,
            to=ctx.caller)

        return "You WON"

    else:
        # Burn percent of bet amount
        I.import_module(token_contract).transfer(
            amount=amount / 100 * burn_rate.get(),
            to=burn_address.get())

        # Send percent of bet amount to reserve
        I.import_module(token_contract).transfer(
            amount=amount / 100 * reserve_rate.get(),
            to=reserve_address.get())

        return "You LOST"

@export
def adjust_burn_rate(percent: float):
    error = "Only owner can adjust burn rate"
    assert ctx.caller == owner.get(), error

    error = "Wrong burn rate value"
    assert (percent >= 0 and percent <= 100), error

    burn_rate.set(percent)

@export
def adjust_reserve_rate(percent: float):
    error = "Only owner can adjust reserve rate"
    assert ctx.caller == owner.get(), error

    error = "Wrong reserve rate value"
    assert (percent >= 0 and percent <= 100), error

    reserve_rate.set(percent)

@export
def adjust_min(amount: int):
    error = "Only owner can adjust min amount"
    assert ctx.caller == owner.get(), error

    min_amount.set(amount)

@export
def adjust_max(amount: int):
    error = "Only owner can adjust max amount"
    assert ctx.caller == owner.get(), error

    max_amount.set(amount)

@export
def pay_in(amount: float, token_contract: str):
    error = "Negative amount is not allowed"
    assert amount > 0, error

    # Transfer tokens from user to contract
    I.import_module(token_contract).transfer_from(
        amount=amount,
        to=ctx.this,
        main_account=ctx.caller)

@export
def pay_out(amount: float, token_contract: str):
    error = "Negative amount is not allowed"
    assert amount > 0, error

    error = "Only owner can payout tokens"
    assert ctx.caller == owner.get(), error

    # Transfer tokens from contract to owner
    I.import_module(token_contract).transfer(
        amount=amount,
        to=ctx.caller)
