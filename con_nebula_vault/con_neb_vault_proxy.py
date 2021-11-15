contracts = Variable()

OPERATOR = '9a12554c2098567d22aaa9b787d73b606d2f2044a602186c3b9af65f6c58cfaf'

@construct
def seed():
	contracts.set([])

@export
def add_contract(contract_name: str):
	assert_owner()

	con_list = contracts.get()
	con_list.append(contract_name)
	contracts.set(set(con_list))

@export
def remove_contract(contract_name: str):
	assert_owner()
	
	con_list = contracts.get()
	if contract_name in con_list: con_list.remove(contract_name)
	contracts.set(con_list)

def assert_owner():
	assert ctx.caller == OPERATOR, 'Only owner can add contracts'
