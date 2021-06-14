import currency as tau
import con_gold_contract as gold

random.seed()

# Owner of this contract
owner = Variable()
# Percent of total pool that goes to dev fund
dev_share = Variable()
# Percent of total pool that goes to endogen
endo_share = Variable()
# Amount of TAU needed to participate
tau_amount = Variable()
# Max users that can participate in one draw
max_entries = Variable()
# How often can one user participate in one draw
user_tickets = Variable()
# Total TAU amount of current run
tau_balance = Variable()
# Total GOLD amount of current run
gold_balance = Variable()
# Overall amount of TAU for Endogen
endo_tau = Variable()
# Overall amount of TAU for devs
dev_tau = Variable()
# List of players for current run
user_list = Variable()
# Last won amount of TAU
last_won_tau = Variable()
# Last won amount of GOLD
last_won_gold = Variable()
# Total won amount of TAU
total_won_tau = Variable()
# Total won amount of GOLD
total_won_gold = Variable()
# Last amount of burned GOLD
last_burned_gold = Variable()
# Total amount of burned GOLD
total_burned_gold = Variable()


@construct
def init():
    owner.set(ctx.caller)
    dev_share.set(9)
    endo_share.set(1)
    tau_amount.set(1)
    max_entries.set(3)
    user_tickets.set(2)
    tau_balance.set(0)
    gold_balance.set(0)
    endo_tau.set(0)
    dev_tau.set(0)
    user_list.set([])
    last_won_tau.set(0)
    last_won_gold.set(0)
    total_won_tau.set(0)
    total_won_gold.set(0)
    last_burned_gold.set(0)
    total_burned_gold.set(0)


@export
def buy_ticket():
    error = "Max users reached. Waiting for winner to be drawn."
    assert len(user_list.get()) < max_entries.get(), error

    tickets = {i: user_list.get().count(i) for i in user_list.get()}

    if ctx.caller in tickets:
        error = "Max amount of tickets per user reached"
        assert tickets[ctx.caller] < user_tickets.get(), error

    # Transfer TAU from user to contract
    tau.transfer_from(
        amount=tau_amount.get(),
        to=ctx.this,
        main_account=ctx.caller)

    tau_balance.set(tau_balance.get() + tau_amount.get())

    gold_price = ForeignHash(
        foreign_contract='con_rocketswap_official_v1_1',
        foreign_name='prices')

    gold_amount = tau_amount.get() / gold_price["con_gold_contract"]

    # Transfer GOLD from user to contract
    gold.transfer_from(
        amount=gold_amount,
        to=ctx.this,
        main_account=ctx.caller)

    gold_balance.set(gold_balance.get() + gold_amount)

    users = user_list.get()
    users.append(ctx.caller)
    user_list.set(users)


@export
def draw_winner():
    allowed = [
        "ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d",
        "aed1eb42d24ccaff3a6264bc07da12170208bbba37b773603b90309ee3fd8b3d",
        "a85b07902b938a37b0501ddd29d1725f99c8daeec6f5f4b4b45b3d801ede599f"
    ]

    error = "Only owner can draw a winner"
    assert ctx.caller in allowed, error

    # Determine winner address
    winner = random.choice(user_list.get())

    dev_amount_tau = tau_balance.get() / 100 * dev_share.get()
    dev_tau.set(dev_tau.get() + dev_amount_tau)

    endo_amount_tau = tau_balance.get() / 100 * endo_share.get()
    endo_tau.set(endo_tau.get() + endo_amount_tau)

    last_burned_gold.set(gold_balance.get() / 100 * (dev_share.get() + endo_share.get()))
    total_burned_gold.set(total_burned_gold.get() + last_burned_gold.get())

    last_won_tau.set(tau_balance.get() - dev_amount_tau - endo_amount_tau)
    last_won_gold.set(gold_balance.get() - last_burned_gold.get())

    total_won_tau.set(total_won_tau.get() + last_won_tau.get())
    total_won_gold.set(total_won_gold.get() + last_won_gold.get())

    # Transfer TAU from contract to winner
    tau.transfer(
        amount=last_won_tau.get(),
        to=winner)

    # Transfer GOLD from contract to winner
    gold.transfer(
        amount=last_won_gold.get(),
        to=winner)

    # Transfer GOLD from contract to burning address
    gold.transfer(
        amount=last_burned_gold.get(),
        to="0000000000000BURN0000000000000")

    # Prepare for next run
    tau_balance.set(0)
    gold_balance.set(0)
    user_list.set([])

    return winner


@export
def set_dev_share(percent: float):
    error = "Only owner can adjust developer share"
    assert ctx.caller == owner.get(), error

    error = "Share can't be less than 0 or more than 100"
    assert (percent >= 0 and percent <= 100), error

    dev_share.set(percent)


@export
def set_endo_share(percent: float):
    error = "Only owner can adjust Endogens share"
    assert ctx.caller == owner.get(), error

    error = "Share can't be less than 0 or more than 100"
    assert (percent >= 0 and percent <= 100), error

    endo_share.set(percent)


@export
def set_tau_amount(amount: int):
    error = "Only owner can adjust TAU amount"
    assert ctx.caller == owner.get(), error

    error = "Amount of TAU can't be negative"
    assert amount >= 0, error

    tau_amount.set(amount)


@export
def set_max_entries(count: int):
    error = "Only owner can adjust max entries"
    assert ctx.caller == owner.get(), error

    error = "Max number of entries must be more than 1"
    assert count > 1, error

    max_entries.set(count)


@export
def set_user_tickets(tickets: int):
    error = "Only owner can adjust number of user tickets"
    assert ctx.caller == owner.get(), error

    error = "Max tickets per user must be more than 0"
    assert tickets >= 1, error

    user_tickets.set(tickets)


@export
def endo_payout():
    error = "Payout only available for owner"
    assert ctx.caller == owner.get(), error

    # Transfer TAU from contract to Endogen
    tau.transfer(
        amount=endo_tau.get(),
        to=ctx.caller)

    endo_tau.set(0)


@export
def dev_payout():
    address = "96dae3b6213fb80eac7c6f4fa0fd26f34022741c56773107b20199cb43f5ed62"

    error = "Payout only available for owner"
    assert ctx.caller == address, error

    # Transfer TAU from contract to Lamden devs
    tau.transfer(
        amount=dev_tau.get(),
        to=ctx.caller)

    dev_tau.set(0)
