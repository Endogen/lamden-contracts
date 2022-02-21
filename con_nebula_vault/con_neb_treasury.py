#  _   _      _           _         _______                                  
# | \ | |    | |         | |       |__   __|                                 
# |  \| | ___| |__  _   _| | __ _     | |_ __ ___  __ _ ___ _   _ _ __ _   _ 
# | . ` |/ _ \ '_ \| | | | |/ _` |    | | '__/ _ \/ _` / __| | | | '__| | | |
# | |\  |  __/ |_) | |_| | | (_| |    | | | |  __/ (_| \__ \ |_| | |  | |_| |
# |_| \_|\___|_.__/ \__,_|_|\__,_|    |_|_|  \___|\__,_|___/\__,_|_|   \__, |
#                                                                       __/ |
# Version 1.0                                                          |___/ 

I = importlib

dex = Variable()
owners = Variable()

@construct
def seed():
    dex.set('con_rocketswap_official_v1_1')

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

@export
def send_token(token_contract: str, amount: float, to: str):
    I.import_module(token_contract).transfer(amount, to)
    assert_owner()

@export
def send_token_to_me(token_contract: str, amount: float):
    I.import_module(token_contract).transfer(amount, ctx.caller)
    assert_owner()

@export
def send_lp(token_contract: str, amount: float, to: str):
    I.import_module(dex.get()).transfer_liquidity(token_contract, to, amount)
    assert_owner()

@export
def send_lp_to_me(token_contract: str, amount: float):
    I.import_module(dex.get()).transfer_liquidity(token_contract, ctx.caller, amount)
    assert_owner()

@export
def set_dex_contract(dex_contract: str):
    dex.set(dex_contract)
    assert_owner()

def assert_owner():
    assert ctx.caller in owners.get(), 'Only executable by Nebula (NEB) team!'
