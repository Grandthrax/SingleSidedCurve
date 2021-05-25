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


def test_wbtc_live_vault(
    wbtc,
    curvePool,
    Strategy,
    hCRV,
    yvault,
    orb,
    rewards,
    chain,
    yhbtcstrategy,
    wbtc_vault,
    ychad,
    whale,
    gov,
    strategist,
    interface,
):

    vault = wbtc_vault
    strategy = strategist.deploy(Strategy, vault, 2 * 1e8)
    currency = wbtc
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    print(currency.balanceOf(whale) / 1e8)
    whalebefore = currency.balanceOf(whale)
    whale_deposit = 2 * 1e8
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(1000)
    chain.mine(1)
    strategy.harvest({"from": strategist})

    # print(strategy.curveTokenToWant(1e8))
    # print(yvault.totalSupply())
    # assert strategy.curveTokensInYVault() == yvault.balanceOf(strategy)
    print(yvault.balanceOf(strategy) / 1e18)
    yvault.earn({"from": ychad})
    print(hCRV.balanceOf(yvault))
    # print("Virtual price: ", hCRV.get_virtual_price())
    # yhbtcstrategy.deposit()
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)

    chain.sleep(2591000)
    chain.mine(1)
    yhbtcstrategy.harvest({"from": orb})
    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print(
        "\nEstimated APR: ",
        "{:.2%}".format(((vault.totalAssets() - 2 * 1e8) * 12) / (2 * 1e8)),
    )
    chain.sleep(21600)  # wait six hours so we get full harvest
    chain.mine(1)

    vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": strategist})

    # vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})

    print("\nWithdraw")
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    balanceAfter = currency.balanceOf(whale)
    print("Whale profit: ", (currency.balanceOf(whale) - whalebefore) / 1e8)
    print(
        "Whale profit %: ",
        "{:.2%}".format(
            ((currency.balanceOf(whale) - whalebefore) / whale_deposit) * 12
        ),
    )


def test_wbtc_1(
    currency,
    Strategy,
    strategy_wbtc_hbtc,
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
    yvault = yvaultv2
    vault = live_wbtc_vault
    currency = interface.ERC20(vault.token())
    gov = accounts.at(vault.governance(), force=True)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    strategy = strategy_wbtc_hbtc
    for i in range(0, 3):
        s = Strategy.at(vault.withdrawalQueue(i))
        vault.updateStrategyDebtRatio(s, 0, {"from": gov})
        s.harvest({"from": gov})

    # strategy = Strategy.at('0x148f64a2BeD9c815EDcD43754d3323283830070c')
    strategist = accounts.at(strategy.strategist(), force=True)
    yvault.setDepositLimit(2 ** 256 - 1, {"from": ychad})
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whalebefore = currency.balanceOf(whale)
    whale_deposit = 2 * 1e8
    assert currency.balanceOf(whale) > whale_deposit
    vault.deposit(whale_deposit, {"from": whale})
    strategy.updateMaxSingleInvest(2 ** 256 - 1, {"from": gov})
    before = vault.totalAssets()
    strategy.harvest({"from": strategist})
    # print(strategy.curveTokenToWant(1e18))
    # print(yvault.totalSupply())
    # assert strategy.curveTokensInYVault() == yvault.balanceOf(strategy)
    # print(yvault.balanceOf(strategy))
    # yvault.earn({'from': ychad})

    yhbtcstrategyv2.harvest({"from": ychad})
    print(hCRV.balanceOf(yvault))
    # yhbtcstrategy.deposit()
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(2592000)
    chain.mine(1)

    yhbtcstrategyv2.harvest({"from": orb})

    chain.sleep(21600)
    chain.mine(1)
    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print(
        "\nEstimated APR: ",
        "{:.2%}".format(((vault.totalAssets() - before) * 12) / (before)),
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

    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)


def test_wbtc_migrate(
    currency,
    Strategy,
    Contract,
    wbtcstrategynew,
    live_strategy_wbtc,
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
    yvault = yvaultv2
    vault = live_wbtc_vault
    currency = interface.ERC20(vault.token())
    gov = accounts.at(vault.governance(), force=True)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    strategy = wbtcstrategynew

    old_strategy = "0x40b04B3ed9845B8Be200Aa2D9C3eDC2bE0a5f01f"
    new_strategy = "0xb85413f6d07454828eAc7E62df7d847316475178"
    wbtc_vault = Contract("0xA696a63cc78DfFa1a63E9E50587C197387FF6C7E")
    wbtc_vault.migrateStrategy(old_strategy, new_strategy, {"from": gov})

    # for i in range(0,3):
    #    s = Strategy.at(vault.withdrawalQueue(i))
    #    vault.updateStrategyDebtRatio(s, 0, {"from": gov})
    #    s.harvest({"from": gov})

    # strategy = Strategy.at('0x148f64a2BeD9c815EDcD43754d3323283830070c')
    strategist = accounts.at(strategy.strategist(), force=True)
    # yvault.setDepositLimit(2**256-1, {'from': ychad})
    debt_ratio = 10_000
    # vault.addStrategy(strategy, debt_ratio,0, 2 ** 256 - 1, 1000, {"from": gov})
    # vault.migrateStrategy(live_strategy_wbtc, strategy, {"from": gov})
    q1 = Strategy.at(vault.withdrawalQueue(0))
    vault.updateStrategyDebtRatio(q1, 6700, {"from": gov})
    vault.updateStrategyDebtRatio(strategy, 1000, {"from": gov})
    q1.harvest({"from": gov})

    # vault.setManagementFee(0, {"from": gov})
    # vault.setPerformanceFee(0, {"from": gov})

    # currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    # whalebefore = currency.balanceOf(whale)
    # whale_deposit  = 2 *1e8
    # assert currency.balanceOf(whale) > whale_deposit
    # vault.deposit(whale_deposit, {"from": whale})
    # strategy.updateMaxSingleInvest(2 ** 256 - 1, {"from": gov})
    # before = vault.totalAssets()
    strategy.harvest({"from": strategist})
    # print(strategy.curveTokenToWant(1e18))
    # print(yvault.totalSupply())
    # assert strategy.curveTokensInYVault() == yvault.balanceOf(strategy)
    # print(yvault.balanceOf(strategy))
    # yvault.earn({'from': ychad})

    # yhbtcstrategyv2.harvest({'from': ychad})
    # print(hCRV.balanceOf(yvault))
    # yhbtcstrategy.deposit()
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    genericStateOfStrat(live_strategy_wbtc, currency, vault)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(2592000)
    chain.mine(1)

    yhbtcstrategyv2.harvest({"from": orb})

    chain.sleep(21600)
    chain.mine(1)
    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    # print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-before)*12)/(before)))
    # chain.sleep(21600)
    # chain.mine(1)

    # vault.transferFrom(strategy, strategist, vault.balanceOf(strategy), {"from": strategist})
    # print("\nWithdraw")
    # vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    # vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": strategist})

    # vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})

    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    # balanceAfter = currency.balanceOf(whale)
    # print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/1e18)
    # print("Whale profit %: ", "{:.2%}".format(((currency.balanceOf(whale) - whalebefore)/whale_deposit)*12))

    # vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    # strategy.harvest({'from': strategist})
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)


# obtc
def test_wbtc_2(
    currency,
    Strategy,
    strategy_wbtc_obtc,
    accounts,
    curvePoolObtc,
    obCRV,
    yvaultv2Obtc,
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
    yvault = yvaultv2Obtc
    vault = live_wbtc_vault
    currency = interface.ERC20(vault.token())
    gov = accounts.at(vault.governance(), force=True)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    strategy = strategy_wbtc_hbtc
    for i in range(0, 3):
        s = Strategy.at(vault.withdrawalQueue(i))
        vault.updateStrategyDebtRatio(s, 0, {"from": gov})
        s.harvest({"from": gov})

    # strategy = Strategy.at('0x148f64a2BeD9c815EDcD43754d3323283830070c')
    strategist = accounts.at(strategy.strategist(), force=True)
    yvault.setDepositLimit(2 ** 256 - 1, {"from": ychad})
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whalebefore = currency.balanceOf(whale)
    whale_deposit = 2 * 1e8
    assert currency.balanceOf(whale) > whale_deposit
    vault.deposit(whale_deposit, {"from": whale})
    strategy.updateMaxSingleInvest(2 ** 256 - 1, {"from": gov})
    before = vault.totalAssets()
    strategy.harvest({"from": strategist})
    # print(strategy.curveTokenToWant(1e18))
    # print(yvault.totalSupply())
    # assert strategy.curveTokensInYVault() == yvault.balanceOf(strategy)
    # print(yvault.balanceOf(strategy))
    # yvault.earn({'from': ychad})

    yhbtcstrategyv2.harvest({"from": ychad})
    print(hCRV.balanceOf(yvault))
    # yhbtcstrategy.deposit()
    # genericStateOfStrat(strategy, currency, vault)
    # genericStateOfVault(vault, currency)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(2592000)
    chain.mine(1)

    yhbtcstrategyv2.harvest({"from": orb})

    chain.sleep(21600)
    chain.mine(1)
    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print(
        "\nEstimated APR: ",
        "{:.2%}".format(((vault.totalAssets() - before) * 12) / (before)),
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

    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    strategy.harvest({"from": strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
