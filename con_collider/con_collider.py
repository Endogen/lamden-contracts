import currency as tau
import con_collider_contract as lhc
import con_rocketswap_official_v1_1 as rswp

random.seed()

owner = Variable()
min_amount = Variable()
max_amount = Variable()


@construct
def init():
    owner.set(ctx.caller)
    min_amount.set(15)
    max_amount.set(50)

@export
def collide(amount: float):
    error = "Min amount is " + str(min_amount.get())
    assert amount >= min_amount.get(), error

    error = "Max amount is " + str(max_amount.get())
    assert amount <= max_amount.get(), error

    tau.transfer_from(
        amount=amount,
        to=ctx.this,
        main_account=ctx.caller)

    rswp_prices = ForeignHash(
        foreign_contract='con_rocketswap_official_v1_1',
        foreign_name='prices')

    lhc_price = rswp_prices["con_collider_contract"]
    lhc_amount = amount / lhc_price

    if random.choice([True, False]):
        tau.transfer(
            amount=amount, 
            to=ctx.caller)

        lhc.transfer(
            amount=lhc_amount, 
            to=ctx.caller)

        return "You won " + str(amount) + " TAU and "  + str(lhc_amount) + " LHC"

    else:
        tau.approve(
            amount=amount,
            to="con_rocketswap_official_v1_1")

        rswp.buy(
            contract="con_collider_contract",
            currency_amount=amount,
            minimum_received=lhc_amount * 0.51,
            token_fees=False)

        return "You lost " + str(amount) + " TAU"

@export
def deposit_tau(amount: float):
    tau.transfer_from(
        amount=amount, 
        to=ctx.this, 
        main_account=ctx.caller)

@export
def withdraw_tau(amount: float):
    error = "Only the owner can withdraw TAU"
    assert owner.get() == ctx.caller, error

    tau.transfer(
        amount=amount, 
        to=ctx.caller)

@export
def deposit_lhc(amount: float):
    lhc.transfer_from(
        amount=amount, 
        to=ctx.this, 
        main_account=ctx.caller)

@export
def withdraw_lhc(amount: float):
    error = "Only the owner can withdraw LHC"
    assert owner.get() == ctx.caller, error

    lhc.transfer(
        amount=amount, 
        to=ctx.caller)

@export
def set_min(amount: float):
    error = "Only the owner can adjust MIN value"
    assert owner.get() == ctx.caller, error

    min_amount.set(amount)

@export
def set_max(amount: float):
    error = "Only the owner can adjust MAX value"
    assert owner.get() == ctx.caller, error

    max_amount.set(amount)
