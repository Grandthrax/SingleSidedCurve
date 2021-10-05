from itertools import count
from brownie import Wei, reverts
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


def test_hbtc_1(
    currency,
    strategy,
    curvePool,
    hCRV,
    yvault,
    orb,
    rewards,
    chain,
    yhbtcstrategy,
    vault,
    ychad,
    whale,
    gov,
    strategist,
    interface,
):
    decimals = currency.decimals()
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whalebefore = currency.balanceOf(whale)
    whale_deposit = 2 * 1e18
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({"from": strategist})
    # print(strategy.curveTokenToWant(1e18))
    # print(yvault.totalSupply())
    # assert strategy.curveTokensInYVault() == yvault.balanceOf(strategy)
    # print(yvault.balanceOf(strategy))
    yvault.earn({"from": ychad})
    print(hCRV.balanceOf(yvault))
    # yhbtcstrategy.deposit()
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)

    chain.sleep(2592000)
    chain.mine(1)
    yhbtcstrategy.harvest({"from": orb})
    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print(
        "\nEstimated APR: ",
        "{:.2%}".format(((vault.totalAssets() - 2 * 1e18) * 12) / (2 * 1e18)),
    )

    chain.sleep(21600)
    chain.mine(1)

    vault.transferFrom(
        strategy, strategist, vault.balanceOf(strategy), {"from": strategist}
    )
    print("\nWithdraw")
    vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": strategist})

    # vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})

    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    balanceAfter = currency.balanceOf(whale)
    print("Whale profit: ", (currency.balanceOf(whale) - whalebefore) / 1e18)
    print(
        "Whale profit %: ",
        "{:.2%}".format(
            ((currency.balanceOf(whale) - whalebefore) / whale_deposit) * 12
        ),
    )


def test_migrate(
    currency,
    Strategy,
    ychad,
    strategy,
    yvault,
    chain,
    vault,
    whale,
    gov,
    strategist,
    interface,
):
    rate_limit = 1_000_000_000 * 1e18
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_deposit = 100 * 1e18
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({"from": strategist})

    yvault.earn({"from": ychad})

    strategy2 = strategist.deploy(Strategy, vault, 2 * 1e8)
    vault.migrateStrategy(strategy, strategy2, {"from": gov})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfStrat(strategy2, currency, vault)
    genericStateOfVault(vault, currency)


def test_reduce_limit(
    currency, Strategy, strategy, chain, vault, whale, gov, strategist, interface
):
    rate_limit = 1_000_000_000 * 1e18
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_deposit = 100 * 1e18
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({"from": strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    vault.revokeStrategy(strategy, {"from": gov})

    strategy.harvest({"from": strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
