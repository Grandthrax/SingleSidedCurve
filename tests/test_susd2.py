from brownie import Wei, reverts, Contract, accounts, chain


def test_susd2(zap_strategy):
    strategy = zap_strategy
    vault = Contract(strategy.vault())
    gov = accounts.at(vault.governance(), True)
    vault = Contract(strategy.vault(), owner=gov)

    s1 = Contract(vault.withdrawalQueue(1))
    s1_debt_ratio = vault.strategies(s1).dict()['debtRatio']
    vault.revokeStrategy(s1)
    s1.harvest({"from": gov})

    vault.addStrategy(strategy, s1_debt_ratio, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    strategy.harvest({"from": gov})

    assert vault.strategies(strategy).dict()["totalDebt"] > 0

    vault.revokeStrategy(strategy)
    strategy.harvest({"from": gov})
    assert vault.strategies(strategy).dict()["totalDebt"] == 0


def test_susd2_clone(zap_strategy):
    vault = Contract("0x7Da96a3891Add058AdA2E826306D812C638D87a7")
    cloned_strategy_address = zap_strategy.cloneSingleSidedCurve(
        vault,
        zap_strategy.strategist(),
        zap_strategy.maxSingleInvest(),
        zap_strategy.minTimePerInvest(),
        zap_strategy.slippageProtectionIn(),
        zap_strategy.curvePool(),
        zap_strategy.zapOut(),
        zap_strategy.curveToken(),
        zap_strategy.yvToken(),
        zap_strategy.poolSize(),
        zap_strategy.metaToken(),
        zap_strategy.hasUnderlying()
    ).return_value

    strategy = Contract.from_abi("Strategy", cloned_strategy_address, zap_strategy.abi)
    gov = accounts.at(vault.governance(), True)
    vault = Contract(vault.address, owner=gov)

    s1 = Contract(vault.withdrawalQueue(1))
    s1_debt_ratio = vault.strategies(s1).dict()['debtRatio']
    vault.revokeStrategy(s1)
    s1.harvest({"from": gov})

    vault.addStrategy(strategy, s1_debt_ratio, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    strategy.harvest({"from": gov})

    assert vault.strategies(strategy).dict()["totalDebt"] > 0

    vault.revokeStrategy(strategy)
    strategy.harvest({"from": gov})
    assert vault.strategies(strategy).dict()["totalDebt"] == 0
