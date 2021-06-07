import pytest
from brownie import Wei, chain, Contract
from eth_abi import encode_single


def test_migrate(
    susd,
    vault,
    cloned_strategy,
    strategy,
    gov,
    susd_whale,
    curvePool,
    curveToken,
    yvault,
    proxy_bytes,
    strategist,
    synth,
    resolver,
):
    token = susd

    amount = 10 * 1e18
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": susd_whale})
    vault.deposit(amount, {"from": susd_whale})
    cloned_strategy.harvest({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()
    assert (
        pytest.approx(cloned_strategy.estimatedTotalAssets(), rel=1e-2)
        == amount * 0.995
    )  # due to exchange fees

    # two harvests are required to get the strategy rolling (due to Synthetix waiting period)
    cloned_strategy.harvest({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()

    # we settle to know how much we will receive in the other strategy
    exchanger = Contract(resolver.getAddress(encode_single("bytes32", b"Exchanger")))
    exchanger.settle(cloned_strategy, encode_single("bytes32", b"sETH"), {"from": gov})
    exchanger.settle(cloned_strategy, encode_single("bytes32", b"sUSD"), {"from": gov})

    # deploy new strategy
    cloned_strategy_2 = strategy.cloneSingleSidedCurve(
        vault,
        curvePool,
        curveToken,
        yvault,
        2,
        False,
        proxy_bytes,
        {"from": strategist},
    ).return_value

    cloned_strategy_2 = Contract.from_abi("Strategy", cloned_strategy_2, strategy.abi)
    cloned_strategy_2.updateSlippageProtectionOut(150, {"from": gov})

    assetsPrev = cloned_strategy.estimatedTotalAssets()
    yvTokenPrev = yvault.balanceOf(cloned_strategy)
    susdPrev = susd.balanceOf(cloned_strategy)
    synthPrev = synth.balanceOf(cloned_strategy)
    curveTokenPrev = curveToken.balanceOf(cloned_strategy)
    curveTokenInVaultPrev = cloned_strategy.curveTokensInYVault()
    vault.migrateStrategy(cloned_strategy, cloned_strategy_2, {"from": gov})
    assert cloned_strategy_2.estimatedTotalAssets() > 0
    assert yvTokenPrev == yvault.balanceOf(cloned_strategy_2)
    assert susdPrev == susd.balanceOf(cloned_strategy_2)
    assert synthPrev == synth.balanceOf(cloned_strategy_2)
    assert curveTokenPrev == curveToken.balanceOf(cloned_strategy_2)
    # assert curveTokenInVaultPrev == cloned_strategy_2.curveTokensInYVault() # yVault pricePerShare changes during strategy migration
    # assert assetsPrev == cloned_strategy_2.estimatedTotalAssets() # yVault pricePerShare changes during strategy migration

    cloned_strategy_2.harvest({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()

    ## check that we can withdraw in full
    cloned_strategy_2.manualRemoveFullLiquidity({"from": gov})
    chain.sleep(6 * 60 + 1)
    chain.mine()

    vault.withdraw({"from": susd_whale})
