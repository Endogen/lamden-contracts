import con_rocketswap_official_v1_1 as rswp
import currency as tau

I = importlib

@export
def buy(token_contract: str, tau_amount: float):
	tau.transfer_from(amount=tau_amount, to=ctx.this, main_account=ctx.signer)
	tau.approve(amount=tau_amount, to='con_rocketswap_official_v1_1')
	rswp.buy(contract=token_contract, currency_amount=tau_amount)
	balances = ForeignHash(foreign_contract=token_contract, foreign_name='balances')
	I.import_module(token_contract).transfer(amount=balances[ctx.this], to=ctx.signer)

@export
def sell(token_contract: str, token_amount: float):
	I.import_module(token_contract).transfer_from(amount=token_amount, to=ctx.this, main_account=ctx.signer)
	I.import_module(token_contract).approve(amount=token_amount, to='con_rocketswap_official_v1_1')
	rswp.sell(contract=token_contract, token_amount=token_amount)
	balances = ForeignHash(foreign_contract='currency', foreign_name='balances')
	tau.transfer(amount=balances[ctx.this], to=ctx.signer)
