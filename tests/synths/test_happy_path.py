import pytest
from brownie import config, Contract, Wei, chain

def test_synth_happy_path(vault, susd, susd_whale, yvault, curvePool, synth, cloned_strategy, gov):
    print("yVault", yvault)
    print("CurvePool", curvePool)
    print("Synth", synth)
    
    # deposit susd in vault
    susd.approve(vault, 2 ** 256 - 1, {'from': susd_whale})
    vault.deposit(Wei("10000 ether"), {'from': susd_whale})

    # harvest
    tx = cloned_strategy.harvest({'from': gov})

    assert yvault.balanceOf(cloned_strategy) > 0
    
    assert False 