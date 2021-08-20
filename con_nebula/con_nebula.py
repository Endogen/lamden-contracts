I = importlib

balances = Hash(default_value=0)
metadata = Hash()

tax_percent = Variable()
swap_allowed = Variable()
vault_contract = Variable()
tax_whitelist = Variable()

SWAP_FACTOR = 0.01
BURN_ADDRESS = 'OH_SHIT_ITS_GONE'
SWAP_END_DATE = now + datetime.timedelta(days=2)
OPERATORS = [
    'ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d',
    'e787ed5907742fa8d50b3ca2701ab8e03ec749ced806a15cdab800a127d7f863'
]

@construct
def seed():
    balances[ctx.caller] = 0

    metadata['token_name'] = "Test-Nebula"
    metadata['token_symbol'] = "TNEB"
    metadata['operator'] = ctx.caller

    tax_percent.set(10)
    swap_allowed.set(False)
    tax_whitelist.set(['con_amm_v9'])
    vault_contract.set('con_test_nebula_vault')

@export
def change_metadata(key: str, value: Any):
    assert_owner()

    metadata[key] = value

@export
def transfer(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'
    assert balances[ctx.caller] >= amount, 'Not enough coins to send!'

    balances[ctx.caller] -= amount

    if to in tax_whitelist.get():
        balances[to] += amount
    else:
        balances[to] += pay_tax_return_rest(amount)

@export
def approve(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'
    balances[ctx.caller, to] += amount

@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, 'Cannot send negative balances!'
    assert balances[main_account, ctx.caller] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'\
        .format(balances[main_account, ctx.caller], amount)
    assert balances[main_account] >= amount, 'Not enough coins to send!'

    balances[main_account, ctx.caller] -= amount
    balances[main_account] -= amount

    if to in tax_whitelist.get():
        balances[to] += amount
    else:
        balances[to] += pay_tax_return_rest(amount)

# ------ TAX & WHITELIST ------

def pay_tax_return_rest(amount: float):
    tax = int(amount / 100 * tax_percent.get())

    if tax > 0:
        balances[vault_contract.get()] += tax
        return amount - tax
    else:
        return amount

@export
def set_transaction_tax(tax: float):
    assert_owner()
    assert (tax_percent.get() >= 0 and tax_percent.get() <= 100), 'Value must be between 0 and 100'

    tax_percent.set(tax)

@export
def add_to_tax_whitelist(contract: str):
    assert_owner()
    assert contract not in tax_whitelist.get(), 'Contract already in tax whitelist!'

    lst = tax_whitelist.get()
    lst.append(contract)
    tax_whitelist.set(lst)

@export
def remove_from_tax_whitelist(contract: str):
    assert_owner()
    assert contract in tax_whitelist.get(), 'Contract not in tax whitelist!'

    lst = tax_whitelist.get()
    lst.remove(contract)
    tax_whitelist.set(lst)

# ------ SWAP ------

@export
def swap_gold(amount: float):
    assert now < SWAP_END_DATE
    assert swap_allowed.get() == True, 'Swapping GOLD for NEB is disabled'
    assert amount > 0, 'Cannot swap negative balances!'

    gold = I.import_module('con_test_gold_contract')
    #gold.approve(amount=amount, to=BURN_ADDRESS)
    gold.transfer_from(amount=amount, to=BURN_ADDRESS, main_account=ctx.caller)
    balances[ctx.caller] += amount * SWAP_FACTOR

@export
def enable_swap():
    assert_owner()
    swap_allowed.set(True)

@export
def disable_swap():
    assert_owner()
    swap_allowed.set(False)

# ------ BURNING ------

@export
def burn_neb(amount: float):
    assert amount > 0, 'Cannot burn negative amount!'
    assert balances[ctx.caller] >= amount, 'Not enough coins to burn!'

    balances[ctx.caller] -= amount

# ------ VAULT ------

@export
def set_vault_contract(contract: str):
    assert_owner()
    vault_contract.set(contract)

# ------ SUPPLY ------

@export
def circulating_supply():
    return int(sum(balances.all()) - balances[BURN_ADDRESS])

@export
def total_supply():
    return int(sum(balances.all()))

# ------ INTERNAL ------

def assert_owner():
    assert ctx.caller in OPERATORS, 'Only executable by operators!'
