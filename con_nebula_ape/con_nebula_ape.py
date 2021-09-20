data = Hash(default_value=0)

active = Variable()
tau_amount = Variable()

price_contract = Variable()
price_variable = Variable()

neb_contract = Variable()
vault_variable = Variable()

INTERNAL_VAULT = 'INTERNAL_NEB_VAULT'
BURN_ADDRESS = 'NEBULA_BURN_ADDRESS'

OPERATORS = [
    'ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d',
    'e787ed5907742fa8d50b3ca2701ab8e03ec749ced806a15cdab800a127d7f863'
]

@construct
def init():
    active.set(False)
    tau_amount.set(1500)

    price_contract.set('con_rocketswap_official_v1_1')
    price_variable.set('prices')
    
    neb_contract.set('con_nebula')
    vault_variable.set('vault_contract')

@export
def subscribe():
    assert active.get() == True, 'Contract disabled'

    neb_price = ForeignHash(foreign_contract=price_contract.get(), foreign_name=price_variable.get())
    neb_amount = int(tau_amount.get() / neb_price[neb_contract.get()])

    neb = importlib.import_module(neb_contract.get())
    neb.transfer_from(amount=neb_amount, to=ctx.this, main_account=ctx.caller)

    data[ctx.caller] += neb_amount
    data[ctx.caller, 'start'] = now

@export
def unsubscribe():
    assert data[ctx.caller] > 0, 'You are not subscribed!'

    total_amount = int(data[ctx.caller])

    time_delta = now - data[ctx.caller, 'start']

    if time_delta <= datetime.timedelta(days=30):
        payout = data[ctx.caller] / 100 * 30
    elif time_delta <= datetime.timedelta(days=90):
        payout = data[ctx.caller] / 100 * 50
    elif time_delta <= datetime.timedelta(days=120):
        payout = data[ctx.caller] / 100 * 70
    else:
        payout = data[ctx.caller] / 100 * 80

    neb = importlib.import_module(neb_contract.get())

    # Pay back user
    neb.transfer(amount=int(payout), to=ctx.caller)

    # Amount of NEB going to the vault
    amount_delta = data[ctx.caller] - payout

    vault = ForeignVariable(foreign_contract=neb_contract.get(), foreign_name=vault_variable.get())

    if not vault.get():
        vault = Variable()
        vault.set(INTERNAL_VAULT)

    # Send delta amount to vault
    neb.transfer(amount=int(amount_delta), to=vault.get())
 
    data[ctx.caller] = 0

    return 'Payed out {} NEB from {} NEB'.format(int(payout), total_amount)

@export
def enable():
    assert_owner()
    active.set(True)

@export
def disable():
    assert_owner()
    active.set(False)

@export
def set_tau_amount(amount: int):
    assert_owner()
    assert amount >= 0, 'Amount of TAU can not be negative'

    tau_amount.set(amount)

@export
def set_price_interface(contract: str, variable: str):
    assert_owner()
    price_contract.set(contract)
    price_variable.set(variable)

@export
def set_vault_interface(contract: str, variable: str):
    assert_owner()
    neb_contract.set(contract)
    vault_variable.set(variable)

def assert_owner():
    assert ctx.caller in OPERATORS, 'Only executable by operators!'
