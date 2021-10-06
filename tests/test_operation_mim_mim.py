from useful_methods import genericStateOfStrat, genericStateOfVault


def test_mim_mim(
    Strategy,
    strategy_mim_mim,
    accounts,
    yvaultv2Mim,
    chain,
    mim_vault,
    gov,
    strategist,
    interface,
):
    strategist = gov
    vault = mim_vault
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_mim_mim

    # Big mim whale!
    whale = accounts.at("0xbbc4A8d076F4B1888fec42581B6fc58d242CF2D5", force=True)

    yvault = yvaultv2Mim
    # amount = 1000*1e6
    # amounts = [0, 0, amount]
    print("curveid: ", strategy.curveId())
    # print("slip: ", strategy._checkSlip(amount))
    # print("expectedOut: ", amount/strategy.virtualPriceToWant())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    yvault.setDepositLimit(2 ** 256 - 1, {"from": yvault.governance()})
    # print("real: ", ibCurvePool.calc_token_amount(amounts, True))
    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    print(currency.name())
    print(whale_before / 1e18)
    whale_deposit = 30_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    # idl = Strategy.at(vault.withdrawalQueue(1))
    # vault.updateStrategyDebtRatio(idl, 0 , {"from": gov})
    # debt_ratio = 2000
    # v0.3.0
    vault.addStrategy(strategy, 10000, 0, 2 ** 256 - 1, 1000, {"from": gov})

    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    print(yvault.pricePerShare() / 1e18)

    ibcrvStrat1 = Strategy.at(yvault.withdrawalQueue(0))
    ibcrvStrat2 = Strategy.at(yvault.withdrawalQueue(1))

    vGov = accounts.at(yvault.governance(), force=True)
    ibcrvStrat1.harvest({"from": vGov})
    ibcrvStrat2.harvest({"from": vGov})
    chain.sleep(2016000)
    chain.mine(1)
    ibcrvStrat1.harvest({"from": vGov})
    ibcrvStrat2.harvest({"from": vGov})
    chain.sleep(21600)
    chain.mine(1)
    print(yvault.pricePerShare() / 1e18)
    strategy.harvest({"from": strategist})
    print(vault.strategies(strategy))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(21600)
    chain.mine(1)

    vault.withdraw(vault.balanceOf(whale), whale, 200, {"from": whale})
    whale_after = currency.balanceOf(whale)
    profit = whale_after - whale_before
    print("profit =", profit / (10 ** (decimals)))
    assert profit > 0
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.setDoHealthCheck(False, {"from": gov})
    # chain.mine(1)

    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)


def test_mim_mim_live(
    Strategy,
    live_strategy_mim_mim,
    accounts,
    yvaultv2Mim,
    chain,
    live_mim_vault,
    gov,
    strategist,
    interface,
):
    strategist = gov
    vault = live_mim_vault
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = live_strategy_mim_mim
    strategist = accounts.at(strategy.strategist(), force=True)

    # Big mim whale!
    whale = accounts.at("0xbbc4A8d076F4B1888fec42581B6fc58d242CF2D5", force=True)

    yvault = yvaultv2Mim
    print("curveid: ", strategy.curveId())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    yvault.setDepositLimit(2 ** 256 - 1, {"from": yvault.governance()})
    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    print(currency.name())
    print(whale_before / 1e18)
    whale_deposit = 30_000 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    print(yvault.pricePerShare() / 1e18)

    ibcrvStrat1 = Strategy.at(yvault.withdrawalQueue(0))
    ibcrvStrat2 = Strategy.at(yvault.withdrawalQueue(1))

    vGov = accounts.at(yvault.governance(), force=True)
    ibcrvStrat1.harvest({"from": vGov})
    ibcrvStrat2.harvest({"from": vGov})
    chain.sleep(2016000)
    chain.mine(1)
    ibcrvStrat1.harvest({"from": vGov})
    ibcrvStrat2.harvest({"from": vGov})
    chain.sleep(21600)
    chain.mine(1)
    print(yvault.pricePerShare() / 1e18)
    strategy.harvest({"from": strategist})
    print(vault.strategies(strategy))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(21600)
    chain.mine(1)

    vault.withdraw(vault.balanceOf(whale), whale, 200, {"from": whale})
    whale_after = currency.balanceOf(whale)
    profit = whale_after - whale_before
    print("profit =", profit / (10 ** (decimals)))
    assert profit > 0
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.setDoHealthCheck(False, {"from": gov})
    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
