from itertools import count
from brownie import Wei, reverts
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat, genericStateOfVault
import random
import brownie


def test_wbtc_obtc(
    wbtc,
    stratms,
    whale,
    Strategy,
    strategy_wbtc_obtc,
    accounts,
    yvaultv2Obtc,
    chain,
    wbtc_vault,
    ychad,
    gov,
    strategist,
    interface,
):
    strategist = gov
    vault = wbtc_vault
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_wbtc_obtc

    yvault = yvaultv2Obtc
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
    whale_deposit = 30 * (10 ** (decimals))
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

    vault.withdraw({"from": whale})
    whale_after = currency.balanceOf(whale)
    print("profit =", (whale_after - whale_before) / (10 ** (decimals)))
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.setDoHealthCheck(False, {"from": gov})
    # chain.mine(1)

    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)


def test_wbtc_obtc_live(
    wbtc,
    stratms,
    whale,
    Strategy,
    live_strategy_wbtc_obtc,
    accounts,
    yvaultv2Obtc,
    chain,
    live_wbtc_vault,
    ychad,
    gov,
    strategist,
    interface,
):

    vault = live_wbtc_vault
    currency = interface.ERC20(vault.token())
    decimals = currency.decimals()
    gov = accounts.at(vault.governance(), force=True)
    strategist = gov
    strategy = live_strategy_wbtc_obtc

    yvault = yvaultv2Obtc
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
    whale_deposit = 30 * (10 ** (decimals))
    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    idl = Strategy.at(vault.withdrawalQueue(1))
    vault.updateStrategyDebtRatio(idl, 0, {"from": gov})
    debt_ratio = 1996
    idl.harvest({"from": gov})
    # v0.3.0
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})

    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)

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
    strategy.harvest({"from": strategist})
    print(vault.strategies(strategy))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(21600)
    chain.mine(1)

    vault.withdraw({"from": whale})
    whale_after = currency.balanceOf(whale)
    print("profit =", (whale_after - whale_before) / (10 ** (decimals)))
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.setDoHealthCheck(False, {"from": gov})
    # chain.mine(1)

    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
