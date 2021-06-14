I = importlib

@export
def send(addresses: list, amount: float, contract: str):
    token = I.import_module(contract)

    for address in addresses:
        token.transfer_from(amount=amount, to=address, main_account=ctx.signer)
