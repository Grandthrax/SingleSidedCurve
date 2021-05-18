from itertools import count
from brownie import Wei, reverts, Contract, accounts, web3
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat, genericStateOfVault
import random
import brownie

# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")


def test_susd_1(
    currency,
    susd,
    live_susd_vault,
    stratms,
    strategy_saave,
    yvaultv2SAAVE,
    Strategy,
    curvePool,
    accounts,
    hCRV,
    yvaultv2,
    orb,
    rewards,
    chain,
    yhbtcstrategyv2,
    live_wbtc_vault,
    ychad,
    whale,
    gov,
    strategist,
    interface,
):
    currency = susd
    decimals = currency.decimals()
    gov = stratms

    vault = live_susd_vault
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_saave

    yvault = yvaultv2SAAVE
    amount = 1_000_000 * 1e18
    amounts = [0, 0, amount]
    print("curveid: ", strategy.curveId())
    print("slip: ", strategy._checkSlip(amount))
    print("expectedOut: ", amount / strategy.virtualPriceToWant())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    yvault.setDepositLimit(2 ** 256 - 1, {"from": yvault.governance()})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    whale_deposit = 1_000_000 * (10 ** (decimals))
    idl = Strategy.at(vault.withdrawalQueue(0))
    idl2 = Strategy.at(vault.withdrawalQueue(1))
    idl.harvest({"from": gov})
    idl2.harvest({"from": gov})
    chain.sleep(6 * 3600 + 1)
    chain.mine(1)

    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    vault.updateStrategyDebtRatio(idl, 0, {"from": gov})
    vault.updateStrategyDebtRatio(idl2, 0, {"from": gov})
    before = vault.totalAssets()

    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    idl.harvest({"from": gov})
    idl2.harvest({"from": gov})
    chain.sleep(6 * 3600 + 1)
    chain.mine(1)

    strategy.harvest({"from": strategist})
    chain.sleep(6 * 3600 + 1)
    chain.mine(1)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    yStrat = Strategy.at(yvault.withdrawalQueue(0))
    vGov = accounts.at(yvault.governance(), force=True)
    yStrat.harvest({"from": vGov})
    days_profit = 365
    chain.sleep(86400 * days_profit)
    chain.mine(1)
    yStrat.harvest({"from": vGov})
    chain.sleep(21600)
    chain.mine(1)
    strategy.harvest({"from": strategist})
    chain.sleep(3600 * 6 + 1)
    chain.mine(1)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    print(
        "\nEstimated APR: ",
        "{:.2%}".format(((vault.totalAssets() - before)) / (before)),
    )

    vault.withdraw(vault.balanceOf(whale), whale, 500, {"from": whale})
    whale_after = currency.balanceOf(whale)
    print("profit =", (whale_after - whale_before) / (10 ** (decimals)))
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(21600)
    chain.mine(1)

    strategy.harvest({"from": strategist})
    chain.sleep(3600 * 6 + 1)
    chain.mine(1)

    genericStateOfStrat(strategy, currency, vault)
