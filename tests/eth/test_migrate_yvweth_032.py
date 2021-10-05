from brownie import Wei, accounts, chain


def test_migrate_yvweth_032(
    live_yvweth_032,
    gov,
    strategy,
    ste_strategy_clone,
    old_seth_strategy,
    old_steth_strategy,
):
    prev_pps = live_yvweth_032.pricePerShare()

    live_yvweth_032.migrateStrategy(old_seth_strategy, strategy, {"from": gov})
    strategy.updateWithdrawProtection(False, {"from": gov})
    tx = strategy.harvest({"from": gov})
    assert tx.events["Harvested"]["loss"] > 0
    assert tx.events["Harvested"]["profit"] == 0
    assert strategy.estimatedTotalAssets() == 0
    assert live_yvweth_032.strategies(strategy).dict()["totalDebt"] == 0

    live_yvweth_032.migrateStrategy(
        old_steth_strategy, ste_strategy_clone, {"from": gov}
    )
    tx = ste_strategy_clone.harvest({"from": gov})
    assert tx.events["Harvested"]["loss"] == 0
    assert tx.events["Harvested"]["profit"] > 0
    assert ste_strategy_clone.estimatedTotalAssets() < 10  # There is some dust :shrug:
    assert live_yvweth_032.strategies(ste_strategy_clone).dict()["totalDebt"] == 0

    chain.sleep(3600 * 8)
    chain.mine(1)
    assert live_yvweth_032.pricePerShare() > prev_pps
