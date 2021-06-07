import pytest
from brownie import Wei, chain


def test_revoke_strategy_from_vault(susd, vault, cloned_strategy, gov, susd_whale):
    strategy = cloned_strategy
    token = susd

    amount = 10 * 1e18
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": susd_whale})
    vault.deposit(amount, {"from": susd_whale})
    strategy.harvest({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=1e-2) == amount * 0.995
    )  # due to exchange fees

    # two harvests are required to get the strategy rolling (due to Synthetix waiting period)
    strategy.harvest({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()

    vault.revokeStrategy(strategy.address, {"from": gov})

    strategy.manualRemoveFullLiquidity({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()

    strategy.harvest({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()
    assert pytest.approx(token.balanceOf(vault.address), rel=1e-2) == amount * 0.995


def test_revoke_strategy_from_strategy(susd, vault, cloned_strategy, gov, susd_whale):
    strategy = cloned_strategy
    token = susd
    amount = 10 * 1e8
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": susd_whale})
    vault.deposit(amount, {"from": susd_whale})
    strategy.harvest({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=1e-2) == amount * 0.995
    )  # due to exchange fees

    # two harvests are required to get the strategy rolling (due to Synthetix waiting period)
    strategy.harvest({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()

    strategy.setEmergencyExit({"from": gov})
    strategy.manualRemoveFullLiquidity({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()
    strategy.harvest({"from": gov})
    assert pytest.approx(token.balanceOf(vault.address), rel=1e-2) == amount * 0.995


def test_revoke_with_profit(
    susd, synth, vault, curveToken, crv_whale, yvault, cloned_strategy, gov, susd_whale
):
    strategy = cloned_strategy
    token = susd
    amount = 10 * 1e8
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": susd_whale})
    vault.deposit(amount, {"from": susd_whale})

    strategy.harvest({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()
    assert (
        pytest.approx(strategy.estimatedTotalAssets(), rel=1e-2) == amount * 0.995
    )  # due to exchange fees

    # two harvests are required to get the strategy rolling (due to Synthetix waiting period)
    strategy.harvest({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()

    curveToken.transfer(yvault, Wei("50000 ether"), {"from": crv_whale})

    profit = (
        cloned_strategy.estimatedTotalAssets()
        - vault.strategies(cloned_strategy).dict()["totalDebt"]
    )
    vault.revokeStrategy(strategy.address, {"from": gov})

    strategy.manualRemoveFullLiquidity({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()
    strategy.harvest({"from": gov})
    if profit > 0:
        assert token.balanceOf(vault.address) > amount
    else:
        assert token.balanceOf(vault.address) < amount
