from brownie import Wei, accounts, chain

def test_increase_ste_allocation_042(live_yvweth_042, gov, ste_strategy_clone_042, seth_strategy_clone_042, old_steth_strategy_042, old_seth_strategy_042):
    live_yvweth_042.migrateStrategy(old_steth_strategy_042, ste_strategy_clone_042, {"from": gov})
    tx = ste_strategy_clone_042.harvest({"from": gov})
    assert tx.events['Harvested']['loss'] == 0
    assert tx.events['Harvested']['profit'] > 0

    chain.sleep(3600*8)
    chain.mine(1)

    live_yvweth_042.updateStrategyDebtRatio(ste_strategy_clone_042, 0, {"from": gov})
    tx = ste_strategy_clone_042.harvest({"from": gov})
    assert live_yvweth_042.strategies(ste_strategy_clone_042).dict()['totalDebt'] == 0
    assert ste_strategy_clone_042.estimatedTotalAssets() < 10

    chain.sleep(3600*8)
    chain.mine(1)

    live_yvweth_042.updateStrategyDebtRatio(ste_strategy_clone_042, 2_000, {"from": gov})
    ste_strategy_clone_042.updateWithdrawProtection(False, {"from": gov})
    tx = ste_strategy_clone_042.harvest({"from": gov})
