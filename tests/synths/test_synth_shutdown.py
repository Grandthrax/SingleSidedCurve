import pytest
from brownie import config, Contract, Wei, chain


def test_synth_shutdown(
    vault, susd, susd_whale, yvault, curvePool, synth, cloned_strategy, gov
):
    # deposit susd in vault
    susd.approve(vault, 2 ** 256 - 1, {"from": susd_whale})
    vault.deposit(Wei("10000 ether"), {"from": susd_whale})

    # harvest
    prev_pps = vault.pricePerShare()
    tx = cloned_strategy.harvest({"from": gov})
    chain.sleep(360 + 1)  # 6 mins
    chain.mine()
    assert synth.balanceOf(cloned_strategy) > 0
    assert yvault.balanceOf(cloned_strategy) == 0
    tx = cloned_strategy.harvest({"from": gov})
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine()
    assert yvault.balanceOf(cloned_strategy) > 0
    assert synth.balanceOf(cloned_strategy) >= 0

    cloned_strategy.manualRemoveFullLiquidity({"from": gov})
    assert susd.balanceOf(cloned_strategy) > 0
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine()

    susd.transfer(vault, Wei("100 ether"), {"from": susd_whale})
    vault.withdraw({"from": susd_whale})
