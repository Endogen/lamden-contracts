# Sender needs to approve contract to spend GOLD
# Set stamps for subscribe() & unsubscribe() to 70

import currency as tau
import con_gold_contract as gold

owner = Variable()
tau_amount = Variable()
data = Hash(default_value=0)
reserve = Variable()
burn = Variable()

@construct
def init():
    owner.set(ctx.caller)
    tau_amount.set(1500)
    reserve.set("96dae3b6213fb80eac7c6f4fa0fd26f34022741c56773107b20199cb43f5ed62")
    burn.set("0000000000000BURN0000000000000")

@export
def subscribe():
    gold_price = ForeignHash(foreign_contract='con_rocketswap_official_v1_1', foreign_name='prices')
    gold_amount = tau_amount.get() / gold_price["con_gold_contract"]

    gold.transfer_from(amount=gold_amount, to=ctx.this, main_account=ctx.caller)

    data[ctx.caller] += gold_amount
    data[ctx.caller, "start"] = now

@export
def unsubscribe():
    time_delta = now - data[ctx.caller, "start"]

    if time_delta <= datetime.timedelta(days=30):
        payout = data[ctx.caller] / 100 * 30
    elif time_delta <= datetime.timedelta(days=90):
        payout = data[ctx.caller] / 100 * 50
    elif time_delta <= datetime.timedelta(days=120):
        payout = data[ctx.caller] / 100 * 70
    else:
        payout = data[ctx.caller] / 100 * 80

    # Pay back user
    gold.transfer(amount=payout, to=ctx.caller)

    amount_delta = data[ctx.caller] - payout

    # Burn half or remaining amount
    gold.transfer(amount=(amount_delta / 2), to=burn.get())

    # Send other half to reserve
    gold.transfer(amount=(amount_delta - (amount_delta / 2)), to=reserve.get())
 
    data[ctx.caller] = 0

    return payout

@export
def set_tau_amount(amount: int):
    assert ctx.caller == owner.get(), "Only owner can adjust TAU amount"
    assert amount >= 0, "Amount of TAU can't be negative"

    tau_amount.set(amount)

@export
def deposit_gold(amount: float):
    gold.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)

@export
def withdraw_gold(amount: float):
    assert owner.get() == ctx.caller, "Only the owner can withdraw GOLD"

    gold.transfer(amount=amount, to=ctx.caller)
