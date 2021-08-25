I = importlib

balances = Hash(default_value=0)
metadata = Hash()

tax_percent = Variable()
swap_allowed = Variable()
vault_contract = Variable()
tax_blacklist = Variable()
total_supply = Variable()

SWAP_FACTOR = 0.01
BURN_ADDRESS = 'NEBULA_BURN_ADDRESS'
INTERNAL_VAULT = 'internal_neb_vault'
GOLD_CONTRACT = 'con_test_gold_contract'
SWAP_END_DATE = now + datetime.timedelta(days=1)
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

    tax_percent.set(1)
    swap_allowed.set(False)
    tax_blacklist.set([])
    vault_contract.set('')
    total_supply.set(0)

@export
def change_metadata(key: str, value: Any):
    assert_owner()

    metadata[key] = value

@export
def transfer(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'
    assert balances[ctx.caller] >= amount, 'Not enough coins to send!'

    balances[ctx.caller] -= amount
    balances[to] += amount

    if to in tax_blacklist.get():
        pay_tax(amount)

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
    balances[to] += amount

    if to in tax_blacklist.get():
        pay_tax(amount)

# ------ TAX ------

def pay_tax(amount: float):
    tax_amount = int(amount / 100 * tax_percent.get())

    if tax_amount > 0:
        difference = int(balances[ctx.signer] - tax_amount)
        assert balances[ctx.signer] >= tax_amount, 'Not enough coins to pay for NEB tax. Missing {} NEB'.format((difference * -1) + 1)

        if not vault_contract.get():
            vault = INTERNAL_VAULT
        else:
            vault = vault_contract.get()

        balances[vault] += tax_amount
        balances[ctx.signer] -= tax_amount

@export
def set_tax(tax_in_percent: float):
    assert_owner()
    assert (tax_in_percent >= 0 and tax_in_percent <= 100), 'Value must be between 0 and 100'

    tax_percent.set(tax_in_percent)

@export
def add_to_tax_blacklist(recipient: str):
    assert_owner()
    assert recipient not in tax_blacklist.get(), 'Recipient already on tax blacklist'

    lst = tax_blacklist.get()
    lst.append(recipient)
    tax_blacklist.set(lst)

@export
def remove_from_tax_blacklist(recipient: str):
    assert_owner()
    assert recipient in tax_blacklist.get(), 'Recipient not on tax blacklist'

    lst = tax_blacklist.get()
    lst.remove(recipient)
    tax_blacklist.set(lst)

# ------ SWAP ------

@export
def swap_gold(amount: float):
    assert now < SWAP_END_DATE, 'Swap period ended'
    assert swap_allowed.get() == True, 'Swapping GOLD for NEB currently disabled'
    assert amount > 0, 'Cannot swap negative balances!'

    gold = I.import_module(GOLD_CONTRACT)
    gold.transfer_from(amount=amount, to=BURN_ADDRESS, main_account=ctx.caller)

    swap_amount = amount * SWAP_FACTOR

    balances[ctx.caller] += swap_amount

    total_supply.set(total_supply.get() + swap_amount)

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
def burn(amount: float):
    assert amount > 0, 'Cannot burn negative amount!'
    assert balances[ctx.caller] >= amount, 'Not enough coins to burn!'

    balances[BURN_ADDRESS] += amount
    balances[ctx.caller] -= amount

# ------ VAULT ------

@export
def set_vault(contract: str):
    assert_owner()
    vault_contract.set(contract)

@export
def flush_internal_vault():
    assert_owner()
    assert vault_contract.get(), 'Vault contract not set!'

    balances[vault_contract.get()] += balances[INTERNAL_VAULT]
    balances[INTERNAL_VAULT] = 0

# ------ SUPPLY ------

@export
def circulating_supply():
    return int(total_supply.get() - balances[BURN_ADDRESS])

@export
def total_supply():
    return int(total_supply.get())

# ------ INTERNAL ------

def assert_owner():
    assert ctx.caller in OPERATORS, 'Only executable by operators!'
