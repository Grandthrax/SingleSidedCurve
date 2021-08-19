from brownie import Wei, accounts, chain

def test_migrate_yvweth_042(live_yvweth_042, gov, ste_strategy_clone_042, seth_strategy_clone_042, old_steth_strategy_042, old_seth_strategy_042):
    prev_pps = live_yvweth_042.pricePerShare()

    live_yvweth_042.migrateStrategy(old_seth_strategy_042, seth_strategy_clone_042, {"from": gov})
    tx = seth_strategy_clone_042.harvest({"from": gov})
    assert tx.events['Harvested']['loss'] > 0
    assert tx.events['Harvested']['profit'] == 0

    live_yvweth_042.migrateStrategy(old_steth_strategy_042, ste_strategy_clone_042, {"from": gov})
    tx = ste_strategy_clone_042.harvest({"from": gov})
    assert tx.events['Harvested']['loss'] == 0
    assert tx.events['Harvested']['profit'] > 0

    chain.sleep(3600*8)
    chain.mine(1)
    assert live_yvweth_042.pricePerShare() > prev_pps
