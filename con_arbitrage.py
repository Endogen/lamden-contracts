import con_rocketswap_official_v1_1 as rswp
import con_reflecttau_v2 as rtau
import currency as tau

metadata = Hash()

@construct
def init(contract_name: str):
	metadata['arb_rate'] = 90
	metadata['operator'] = ctx.caller
	metadata['contract'] = contract_name

@export
def get_lp(tau_amount: float):
	tau_buy_amount = tau_amount / 100 * int(metadata['arb_rate'])
	tau_transfered = int(tau_buy_amount) + 1

	prices = ForeignHash(foreign_contract='con_rocketswap_official_v1_1', foreign_name='prices')
	rtau_price = prices['con_reflecttau_v2']; basic_price = prices['con_doug_lst001']

	basic_buy_amount = tau_buy_amount / basic_price
	tau_received = ((basic_buy_amount * 0.07613035) * rtau_price) * 0.8
	assert tau_received > tau_transfered, f'{tau_received - tau_transfered}'

	tau.transfer_from(amount=tau_transfered, to=metadata['contract'], main_account=ctx.caller)
	rtau.swap_basic(basic_amount=rswp.buy(contract='con_doug_lst001', currency_amount=tau_buy_amount))
	rswp.sell(contract='con_reflecttau_v2', token_amount=rtau.balance_of(address=metadata['contract']))

	tau_balance = tau.balance_of(account=metadata['contract'])
	return f'{int(tau_balance)}'

@export
def get_balance():
	assert_caller_is_operator();
	tau_balance = tau.balance_of(account=metadata['contract'])
	tau.transfer(amount=tau_balance, to=ctx.caller)
	return f'{int(tau_balance)}'

@export
def change_metadata(key: str, value: Any):
    assert_caller_is_operator()
    metadata[key] = value

def assert_caller_is_operator():
	assert ctx.caller == metadata['operator'], 'Not allowed!'

# {"contract_name":"con_check_lp2"}