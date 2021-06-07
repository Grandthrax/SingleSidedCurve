import pytest
from brownie import Wei, chain, Contract
from eth_abi import encode_single


def test_quick_harvest(
    vault,
    cloned_strategy,
    susd,
    susd_whale,
    synth,
    yvault,
    gov,
    curveToken,
    curvePool,
    crv_whale,
):
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
    # it should respect the buffer
    assert (
        susd.balanceOf(cloned_strategy) * 10
        == vault.strategies(cloned_strategy).dict()["totalDebt"]
    )
    chain.sleep(360 + 1)  # over 6 mins
    chain.mine(1)

    # harvest again to add liquidity
    cloned_strategy.harvest({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()

    assert yvault.balanceOf(cloned_strategy) > 0
    assert susd.balanceOf(cloned_strategy) * 10 == pytest.approx(
        vault.strategies(cloned_strategy).dict()["totalDebt"], rel=1e-8
    )
    cloned_strategy.updateMinTimePerInvest(1000, {"from": gov})
    # assert False
    print("Initial state")
    print_status(cloned_strategy, vault, susd, synth, yvault, None)
    assert pytest.approx(susd.balanceOf(cloned_strategy) * 10000, rel=1e-10) == (
        cloned_strategy.susdBuffer()
        * vault.strategies(cloned_strategy).dict()["totalDebt"]
    )
    tx = cloned_strategy.harvest({"from": gov})
    print("Harvested. Should take profit from balancing the pool")
    print_status(cloned_strategy, vault, susd, synth, yvault, tx)
    assert (
        cloned_strategy.estimatedTotalAssets()
        - vault.strategies(cloned_strategy).dict()["totalDebt"]
    ) == 0  # current profit

    prevProfit = (
        cloned_strategy.estimatedTotalAssets()
        - vault.strategies(cloned_strategy).dict()["totalDebt"]
    ) / 1e18
    print("Prev eCRV PSS", yvault.pricePerShare())
    curveToken.transfer(yvault, Wei("100 ether"), {"from": crv_whale})
    print("Post eCRV PSS", yvault.pricePerShare())
    vault.deposit(Wei("10000 ether"), {"from": susd_whale})
    print("Someone deposited + strategy generated profit")
    assert (
        prevProfit
        < (
            cloned_strategy.estimatedTotalAssets()
            - vault.strategies(cloned_strategy).dict()["totalDebt"]
        )
        / 1e18
    )
    print_status(cloned_strategy, vault, susd, synth, yvault, tx)

    tx = cloned_strategy.harvest({"from": gov})
    print("Harvested again to receive funds from vault. Should not invest (too soon)")
    print_status(cloned_strategy, vault, susd, synth, yvault, tx)
    assert tx.events["Harvested"]["profit"] > 0

    chain.sleep(1000 + 1)
    chain.mine()
    print("Sleep for an hour...")
    prevYToken = yvault.balanceOf(cloned_strategy)
    tx = cloned_strategy.harvest({"from": gov})
    print("Harvested. Should invest funds (exchange sUSD for sETH)")
    print_status(cloned_strategy, vault, susd, synth, yvault, tx)
    assert prevYToken < yvault.balanceOf(
        cloned_strategy
    )  # it also invests some of the previously available sETH

    prevYToken = yvault.balanceOf(cloned_strategy)
    tx = cloned_strategy.harvest({"from": gov})
    print("Harvested. Should do nothing regarding sETH (too soon)")
    print_status(cloned_strategy, vault, susd, synth, yvault, tx)
    assert prevYToken == yvault.balanceOf(cloned_strategy)

    chain.sleep(1000 + 1)
    chain.mine()
    print("Slept for 1 hour")

    prevYToken = yvault.balanceOf(cloned_strategy)
    tx = cloned_strategy.harvest({"from": gov})
    print("Harvested. Should add liquidity to curve")

    assert prevYToken < yvault.balanceOf(cloned_strategy)
    print_status(cloned_strategy, vault, susd, synth, yvault, tx)


def print_status(strat, vault, susd, synth, yvault, tx):
    print(
        f"\tProfit {(strat.estimatedTotalAssets()-vault.strategies(strat).dict()['totalDebt'])/1e18}"
    )
    print(
        f"\tBuffer {(strat.susdBuffer()*vault.strategies(strat).dict()['totalDebt'])/1e18/10000}"
    )
    print(f"\tBalance of susd {susd.balanceOf(strat)/1e18}")
    print(f"\tBalance of synth {synth.balanceOf(strat)/1e18}")
    print(f"\tBalance of yvToken {yvault.balanceOf(strat)/1e18}")
    if tx:
        print(f"\tHarvested profit {tx.events['Harvested']['profit']}")
        print(f"\tHarvested loss {tx.events['Harvested']['loss']}")
