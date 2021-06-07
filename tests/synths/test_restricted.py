import pytest
from brownie import config, Contract, Wei, chain, reverts


def test_restricted(susd_whale, strategy, live_susd_vault):
    rando = susd_whale
    gov = live_susd_vault.governance()
    with reverts():
        strategy.updateMinTimePerInvest(0, {"from": rando})
    strategy.updateMinTimePerInvest(0, {"from": strategy.strategist()})
    strategy.updateMinTimePerInvest(0, {"from": gov})

    with reverts():
        strategy.updateSUSDBuffer(0, {"from": rando})
    strategy.updateSUSDBuffer(0, {"from": strategy.strategist()})
    strategy.updateSUSDBuffer(0, {"from": gov})

    with reverts():
        strategy.updatemaxSingleInvest(0, {"from": rando})
    strategy.updatemaxSingleInvest(0, {"from": strategy.strategist()})
    strategy.updatemaxSingleInvest(0, {"from": gov})

    with reverts():
        strategy.updateSlippageProtectionIn(0, {"from": rando})
    strategy.updateSlippageProtectionIn(0, {"from": strategy.strategist()})
    strategy.updateSlippageProtectionIn(0, {"from": gov})

    with reverts():
        strategy.updateSlippageProtectionOut(0, {"from": rando})
    strategy.updateSlippageProtectionOut(0, {"from": strategy.strategist()})
    strategy.updateSlippageProtectionOut(0, {"from": gov})

    with reverts():
        strategy.updateMaxLoss(0, {"from": rando})
    strategy.updateMaxLoss(0, {"from": strategy.strategist()})
    strategy.updateMaxLoss(0, {"from": gov})
