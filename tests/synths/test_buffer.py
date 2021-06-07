import pytest
from brownie import config, Contract, Wei, chain, reverts


def test_buffer(
    vault,
    susd,
    susd_whale,
    yvault,
    curveToken,
    curvePool,
    crv_whale,
    synth,
    cloned_strategy,
    gov,
):
    print("yVault", yvault)
    print("CurvePool", curvePool)
    print("Synth", synth)

    # deposit susd in vault
    susd.approve(vault, 2 ** 256 - 1, {"from": susd_whale})
    vault.deposit(Wei("10000 ether"), {"from": susd_whale})

    # harvest
    # first harvest will only invest sUSD in sETH
    # afterwards, both actions will be done
    prev_pps = vault.pricePerShare()
    tx = cloned_strategy.harvest({"from": gov})
    assert yvault.balanceOf(cloned_strategy) == 0
    assert synth.balanceOf(cloned_strategy) > 0
    assert susd.balanceOf(cloned_strategy) > 0
    assert (
        susd.balanceOf(cloned_strategy)
        == vault.strategies(cloned_strategy).dict()["totalDebt"] * 0.1
    )
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine(1)

    # simulate profit to avoid losses in accounting
    print("Prev eCRV PSS", yvault.pricePerShare())
    # if synth.symbol() == "sEUR":
    #     curveToken.transfer(yvault, Wei("1000 ether"), {"from": crv_whale})
    curveToken.transfer(yvault, Wei("10 ether"), {"from": crv_whale})
    print("Post eCRV PSS", yvault.pricePerShare())

    # harvest to invest and go to steady state
    tx = cloned_strategy.harvest({"from": gov})  # this harvest will record profits
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine(1)
    tx = cloned_strategy.harvest(
        {"from": gov}
    )  # we harvest again to manage initial changes and get to steady state
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine(1)

    # NOW THE TEST BEGINS
    # cannot set it higher than 100%
    with reverts():
        cloned_strategy.updateSUSDBuffer(10_001, {"from": gov})

    # up to 25% buffer (from 10%)
    print("10% -> 25%")
    cloned_strategy.updateSUSDBuffer(2_500, {"from": gov})
    # vault.deposit(Wei("10000 ether"), {"from": susd_whale})
    if synth.symbol == "sEUR":
        vault.deposit(Wei("1000 ether"), {"from": susd_whale})
    else:  # sETH sLINK
        vault.deposit(Wei("10000 ether"), {"from": susd_whale})
    tx = cloned_strategy.harvest({"from": gov})
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine(1)
    assert susd.balanceOf(cloned_strategy) * 4 == pytest.approx(
        vault.strategies(cloned_strategy).dict()["totalDebt"]
    )

    # back down to 10% (from 25%)
    cloned_strategy.updateSUSDBuffer(1_000, {"from": gov})
    print("25% -> 10%")

    # this harvest should invest the amount of buffer that we don't require anymore
    tx = cloned_strategy.harvest({"from": gov})
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine(1)
    assert (
        tx.events["ExchangeEntryAppended"]["dest"] == cloned_strategy.synthCurrencyKey()
    )  # an exchange (sUSD => sETH) happened
    assert tx.events["ExchangeEntryAppended"]["amount"] >= 0.15 * (
        vault.strategies(cloned_strategy).dict()["totalDebt"]
    )
    assert susd.balanceOf(cloned_strategy) * 10 == pytest.approx(
        vault.strategies(cloned_strategy).dict()["totalDebt"]
    )

    # go to 100% buffer (any new amount that gets into the strategy is not invested) (from 10%)
    cloned_strategy.updateSUSDBuffer(10_000, {"from": gov})
    print("10% -> 100%")

    # new deposits should directly increase susd balance, not yvault balance
    # strategy will uninvest the full balance to be able to honor the sUSD buffer
    if synth.symbol == "sEUR":
        vault.deposit(Wei("500 ether"), {"from": susd_whale})
    else:  # sETH sLINK
        vault.deposit(Wei("50000 ether"), {"from": susd_whale})
    prevBalance = susd.balanceOf(cloned_strategy)
    tx = cloned_strategy.harvest({"from": gov})
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine(1)
    assert yvault.balanceOf(cloned_strategy) <= 5  # rounding errors
    assert prevBalance < susd.balanceOf(cloned_strategy)
    # go to 0% buffer (no amount of sUSD is kept uninvested) (from 100%)
    cloned_strategy.updateSUSDBuffer(0, {"from": gov})
    print("100% -> 0%")

    # two harvests required to 1) exchange for sETH 2) deposit in curve's pool
    tx = cloned_strategy.harvest({"from": gov})
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine(1)
    # should revert as it does not have enough to serve profits / other repaymetns
    if (
        cloned_strategy.estimatedTotalAssets()
        - vault.strategies(cloned_strategy).dict()["totalDebt"]
        > 0
    ):
        with reverts():
            tx = cloned_strategy.harvest({"from": gov})
            chain.sleep(360 + 1)  # over 6 mins
            chain.mine(1)

    # if buffer gets to 0, the strategy might get stuck! we need manual liquidation
    cloned_strategy.manualRemoveFullLiquidity({"from": gov})
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine(1)
    # back to 10%
    cloned_strategy.updateSUSDBuffer(1_000, {"from": gov})
    print("0% -> 10%")
    tx = cloned_strategy.harvest({"from": gov})
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine(1)
    assert susd.balanceOf(cloned_strategy) * 10 == pytest.approx(
        vault.strategies(cloned_strategy).dict()["totalDebt"]
    )
    assert (
        vault.strategies(cloned_strategy).dict()["totalLoss"]
        < vault.strategies(cloned_strategy).dict()["totalDebt"] * 0.02
    )  # which will come from big exchanges with no profits
