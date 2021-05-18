from itertools import count
from brownie import Wei, reverts, Contract, accounts, web3
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")
def clone_strategy(strategy_to_clone, vault):
    ms = accounts.at(web3.ens.resolve("brain.ychad.eth"), force=True)
    # susd_vault = Contract("0xa5cA62D95D24A4a350983D5B8ac4EB8638887396", owner=ms)
    # assert susd_vault.token() == "0x57Ab1ec28D129707052df4dF418D58a2D46d5f51"
    sam = "0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0"
    juan = "0xB28Af40C766044915d6f45313d2A8d94481F646F"
    poolpi = "0x740d25cFda3aF381D90B6800C245E670E7841cd8"
    sharer_v4 = Contract.from_explorer("0xc491599b9A20c3A2F0A85697Ee6D9434EFa9f503", owner=ms)

    single_side_to_clone = strategy_to_clone
    assert single_side_to_clone.name() == "SingleSidedCrvWBTC"

    max_single_invest = 1_500_000 * 1e18 # in BTC one this was 30 BTC
    min_time_per_invest = 3600 # same params HBTC
    slippage_protection_in = 500
    curvePool = "0xEB16Ae0052ed37f479f7fe63849198Df1765a733" #
    curveToken = "0x02d341CcB60fAaf662bC0554d13778015d1b285C" # 
    yvToken = "0xb4D1Be44BfF40ad6e506edf43156577a3f8672eC" # crvSAAVE
    poolSize = 2 # aSUSD, aDAI
    hasUnderlying = True
    print(single_side_to_clone, vault)
    tx_cloned_ss_strategy = single_side_to_clone.cloneSingleSidedCurve(
        vault, 
        juan, 
        sharer_v4, 
        poolpi, 
        max_single_invest, 
        min_time_per_invest, 
        slippage_protection_in, 
        curvePool,
        curveToken, 
        yvToken, 
        poolSize,
        hasUnderlying, 
        {'from': juan}
    )
    cloned_strategy_address = tx_cloned_ss_strategy.events["Cloned"]["clone"]
    cloned_ss_strategy = Contract.from_abi(
        "Strategy", cloned_strategy_address, single_side_to_clone.abi, owner=ms
    )

    sharer_v4.setContributors(
        cloned_ss_strategy,
        [juan, poolpi, sam, ms],
        [100, 100, 500, 300],
    )

    return cloned_ss_strategy

def test_susd_1(currency, susd, live_susd_vault,stratms, strategy_saave, yvaultv2SAAVE, Strategy,curvePool, accounts, hCRV,yvaultv2, orb,rewards,chain,yhbtcstrategyv2,live_wbtc_vault, ychad, whale,gov,strategist, interface):
    currency = susd
    decimals = currency.decimals()
    gov = stratms
    
    vault = live_susd_vault
    gov = accounts.at(vault.governance(), force=True)
    strategy = strategy_saave

    yvault = yvaultv2SAAVE
    amount = 1_000_000*1e18
    amounts = [0, 0, amount]
    print("curveid: ", strategy.curveId())
    print("slip: ", strategy._checkSlip(amount))
    print("expectedOut: ", amount/strategy.virtualPriceToWant())
    print("curve token: ", strategy.curveToken())
    print("ytoken: ", strategy.yvToken())
    yvault.setDepositLimit(2 **256 -1 , {'from': yvault.governance()})
    vault.setDepositLimit(2 **256 -1 , {'from': gov})
    #print("real: ", ibCurvePool.calc_token_amount(amounts, True))
    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    whale_before = currency.balanceOf(whale)
    whale_deposit = 1_000_000 * (10 ** (decimals))
    idl = Strategy.at(vault.withdrawalQueue(0))
    idl.harvest({'from': gov})
    chain.sleep(6*3600+1)
    chain.mine(1)

    vault.deposit(whale_deposit, {"from": whale})
    vault.setManagementFee(0, {"from": gov})

    vault.updateStrategyDebtRatio(idl, 0 , {"from": gov})
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    idl.harvest({'from': gov})
    chain.sleep(6*3600+1)
    chain.mine(1)

    strategy.harvest({'from': strategist})
    chain.sleep(6*3600+1)
    chain.mine(1)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    yStrat = Strategy.at(yvault.withdrawalQueue(0))
    gauge = Contract("0x462253b8f74b72304c145db0e4eebd326b22ca39")
    proxy = Contract("0x9a165622a744c20e3b2cb443aed98110a33a231b")
    proxy.approveStrategy(gauge, yStrat, {'from': "0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52"})
    vGov = accounts.at(yvault.governance(), force=True)
    yStrat.harvest({"from": vGov})
    chain.sleep(201600)
    chain.mine(1)
    yStrat.harvest({"from": vGov})
    chain.sleep(21600)
    chain.mine(1)
    strategy.harvest({'from': strategist})
    chain.sleep(3600*6+1)
    chain.mine(1)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    vault.withdraw(vault.balanceOf(whale), whale, 10_000, {"from": whale})
    whale_after = currency.balanceOf(whale)
    print("profit =", (whale_after - whale_before)/(10 ** (decimals)))
    print("balance left =", vault.balanceOf(whale))
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(21600)
    chain.mine(1)

    strategy.harvest({'from': strategist})
    chain.sleep(3600*6+1)
    chain.mine(1)

    genericStateOfStrat(strategy, currency, vault)