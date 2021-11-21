I = importlib

owners = Variable()

@construct
def seed():
    owners.set([
        'ae7d14d6d9b8443f881ba6244727b69b681010e782d4fe482dbfb0b6aca02d5d',
        'e787ed5907742fa8d50b3ca2701ab8e03ec749ced806a15cdab800a127d7f863'
    ])

@export
def add_owner(address: str):
    assert_owner()

    owner_list = owners.get()
    
    if address not in owner_list:
        owner_list.append(address)
        owners.set(owner_list)

@export
def remove_owner(address: str):
    assert_owner()

    owner_list = owners.get()
    
    if address in owner_list:
        owner_list.remove(address)
        owners.set(owner_list)

# TODO: Wieso bekomme ich "Not enough coins" Error?
@export
def withdraw_token(contract: str, amount: float, to: str = ''):
    I.import_module(contract).transfer(amount, validate(determine(to)))
    assert_owner()

@export
def withdraw_lp(contract: str, amount: float, to: str = ''):
    I.import_module(con['dex']).transfer_liquidity(contract, validate(determine(to)), amount)w21q                       
    assert_owner()

def validate(recipient: str):
    if recipient.lower().startswith("con_"):
        assert len(recipient) == 64, 'Address is not valid!'
        # Runs into ImportError
        assert I.import_module(recipient), 'Contract does not exist!'
    else:
        # Runs into ValueError
        assert int(recipient, 16), 'Address is not a valid hex (base 16) string!'

def determine(address: str):
    return address if address else ctx.caller

def assert_owner():
    assert ctx.caller in owners.get(), 'Only executable by Nebula (NEB) team!'
