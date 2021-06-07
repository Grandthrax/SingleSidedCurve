import pytest
from brownie import config, Contract, Wei, chain


def test_synth_happy_path(
    vault,
    susd,
    susd_whale,
    yvault,
    curvePool,
    synth,
    cloned_strategy,
    curveToken,
    gov,
    crv_whale,
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
    tx = cloned_strategy.harvest(
        {"from": gov}
    )  # this harvest will record losses from exchange fees, reducing debt ratio
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine(1)
    assert yvault.balanceOf(cloned_strategy) > 0
    assert synth.balanceOf(cloned_strategy) > 0

    # simulate profit in yVault
    print("Prev eCRV PSS", yvault.pricePerShare())
    curveToken.transfer(yvault, Wei("50 ether"), {"from": crv_whale})
    print("Post eCRV PSS", yvault.pricePerShare())

    # this harvest will effectively reduce the debt due to losses from previous harvests
    tx = cloned_strategy.harvest({"from": gov})
    chain.sleep(360 + 1)
    chain.mine()

    # simulate huge profit (higher than buffer)
    print("Prev eCRV PSS", yvault.pricePerShare())
    amount = curveToken.balanceOf(crv_whale) / 4
    if synth.symbol() == "sETH":
        amount = Wei("50000 ether")
    elif synth.symbol() == "sEUR":
        amount = Wei("5000 ether")

    curveToken.transfer(yvault, amount, {"from": crv_whale})
    print("Post eCRV PSS", yvault.pricePerShare())

    # this harvest will pay less profit than it actually has because buffer is not enough
    actual_profit = (
        cloned_strategy.estimatedTotalAssets()
        - vault.strategies(cloned_strategy).dict()["totalDebt"]
    )
    loose_susd = susd.balanceOf(cloned_strategy)
    tx = cloned_strategy.harvest({"from": gov})
    chain.sleep(360 + 1)
    chain.mine()
    # assert tx.events["Harvested"]["profit"] == loose_susd
    # assert tx.events["Harvested"]["profit"] < actual_profit
    # susd balance is not 0 because we add debt (that is used to refill buffer)

    # another deposit will refill the buffer
    vault.deposit(Wei("100000 ether"), {"from": susd_whale})

    loose_susd = susd.balanceOf(cloned_strategy)
    actual_profit = (
        cloned_strategy.estimatedTotalAssets()
        - vault.strategies(cloned_strategy).dict()["totalDebt"]
    )
    tx = cloned_strategy.harvest({"from": gov})
    chain.sleep(360 + 1)
    chain.mine()
    assert synth.balanceOf(cloned_strategy) > 0
    assert susd.balanceOf(cloned_strategy) > 0  # buffer
    # some profit will be repaid as the last vault.report sent some profit back
    # assert tx.events["Harvested"]["profit"] == loose_susd

    # now there is enough buffer to repay profit
    loose_susd = susd.balanceOf(cloned_strategy)
    actual_profit = (
        cloned_strategy.estimatedTotalAssets()
        - vault.strategies(cloned_strategy).dict()["totalDebt"]
    )
    assert loose_susd > actual_profit
    # it repays profit in vault.report and then should refill the buffer
    tx = cloned_strategy.harvest({"from": gov})
    chain.sleep(360 + 1)
    chain.mine()

    assert vault.strategies(cloned_strategy).dict()["totalDebt"] * 0.1 == pytest.approx(
        susd.balanceOf(cloned_strategy)
    )
