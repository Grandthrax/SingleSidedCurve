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
        hasUnderlying
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

def test_susd_1(currency, susd_vault, yvaultv2SAAVE, Strategy,curvePool, accounts, hCRV,yvaultv2, orb,rewards,chain,yhbtcstrategyv2,live_wbtc_vault, ychad, whale,gov,strategist, interface):
    yvault = yvaultv2SAAVE
    vault = susd_vault
    currency = interface.ERC20(vault.token())
    gov = accounts.at(vault.governance(), force=True)
    vault.setDepositLimit(2**256-1, {"from": gov})
    #strategy = strategist.deploy(Strategy, vault, 2*1e18)
    strategy_to_clone = Contract('0x40b04B3ed9845B8Be200Aa2D9C3eDC2bE0a5f01f')

    strategy = clone_strategy(strategy_to_clone, vault)

    strategist = accounts.at(strategy.strategist(), force=True)
    yvault.setDepositLimit(2**256-1, {'from': ychad})
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio,0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 2 * 1e18
    assert currency.balanceOf(whale) > whale_deposit
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': strategist})
    print(strategy.curveTokenToWant(1e18))
    print(yvault.totalSupply())
    assert strategy.curveTokensInYVault() == yvault.balanceOf(strategy)
    print(yvault.balanceOf(strategy))
    yvault.earn({'from': ychad})

    yhbtcstrategyv2.harvest({'from': ychad})
    print(hCRV.balanceOf(yvault))
    #yhbtcstrategy.deposit()
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(2592000)
    chain.mine(1)

    yhbtcstrategyv2.harvest({'from': orb})
    
    chain.sleep(21600)
    chain.mine(1)
    strategy.harvest({'from': strategist})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-2*1e18)*12)/(2*1e18)))
    chain.sleep(21600)
    chain.mine(1)
    
    vault.transferFrom(strategy, strategist, vault.balanceOf(strategy), {"from": strategist})
    print("\nWithdraw")
    vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": strategist})

    #vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})


    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    balanceAfter = currency.balanceOf(whale)
    print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/1e18)
    print("Whale profit %: ", "{:.2%}".format(((currency.balanceOf(whale) - whalebefore)/whale_deposit)*12))

def _mmEarnAndHarvest(mmKeeper, mmVault, mmStrategy): 
    mmVault.earn({"from": mmKeeper})    

    mmStrategy.harvest({"from": mmKeeper})  

def test_mando(currency,Strategy,Contract, accounts, hCRV,yvaultv2, orb,rewards,chain,yhbtcstrategyv2,live_wbtc_vault, ychad, whale,gov,strategist, interface):
    vault = live_wbtc_vault
    strategy = Contract.from_explorer('0x53a65c8e238915c79a1e5C366Bc133162DBeE34f')
    currency = interface.ERC20(vault.token())
    gov = accounts.at(vault.governance(), force=True)
    vault.setDepositLimit(2**256-1, {"from": gov})
    
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio,0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 2 *1e18
    assert currency.balanceOf(whale) > whale_deposit
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': gov})
    mmVault = Contract.from_explorer("0xb06661A221Ab2Ec615531f9632D6Dc5D2984179A")
    mmKeeper = accounts.at("0x7cDaCBa026DDdAa0bD77E63474425f630DDf4A0D", force=True)
    mmStrategy = Contract.from_explorer("0xc8EBBaAaD5fF2e5683f8313fd4D056b7Ff738BeD")
    _mmEarnAndHarvest(mmKeeper, mmVault, mmStrategy)

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    chain.mine(276)

    _mmEarnAndHarvest(mmKeeper, mmVault, mmStrategy)
    
    strategy.harvest({'from': gov})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-2*1e18)*8760)/(2*1e18)))
    chain.sleep(21600)
    chain.mine(1)
    
    #vault.transferFrom(strategy, strategist, vault.balanceOf(strategy), {"from": gov})
    print("\nWithdraw")
    #vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    #vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": gov})
    vault.revokeStrategy(strategy, {"from": gov})
    strategy.harvest({'from': gov})

    #vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})


    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    balanceAfter = currency.balanceOf(whale)
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    #print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/1e18)
    #print("Whale profit %: ", "{:.2%}".format(((currency.balanceOf(whale) - whalebefore)/whale_deposit)*12))


def test_wbtc_live_vault(wbtc, curvePool,Strategy, hCRV,yvault, orb,rewards,chain,yhbtcstrategy,wbtc_vault, ychad, whale,gov,strategist, interface):

    vault = wbtc_vault
    strategy = strategist.deploy(Strategy, vault, 2*1e18)
    currency = interface.ERC20(vault.token())
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    print(currency.balanceOf(whale)/1e18)
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 2 *1e18
    vault.deposit(whale_deposit, {"from": whale})
    strategy.harvest({'from': gov})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    chain.sleep(1000)
    chain.mine(1)
    strategy.harvest({'from': gov})

    #print(strategy.curveTokenToWant(1e18))
    #print(yvault.totalSupply())
    #assert strategy.curveTokensInYVault() == yvault.balanceOf(strategy)
    print(yvault.balanceOf(strategy)/1e18)
    yvault.earn({'from': ychad})
    print(hCRV.balanceOf(yvault))
    #print("Virtual price: ", hCRV.get_virtual_price())
    #yhbtcstrategy.deposit()
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)

    chain.sleep(2591000)
    chain.mine(1)
    yhbtcstrategy.harvest({'from': orb})
    strategy.harvest({'from': gov})
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-2*1e18)*12)/(2*1e18)))
    chain.sleep(21600) # wait six hours so we get full harvest
    chain.mine(1)

    vault.withdraw(vault.balanceOf(whale), whale, 100, {"from": whale})
    #vault.withdraw(vault.balanceOf(strategist), strategist, 100, {"from": strategist})

    #vault.withdraw(vault.balanceOf(rewards), rewards, 100, {"from": rewards})

    print("\nWithdraw")
    #genericStateOfStrat(strategy, currency, vault)
    #genericStateOfVault(vault, currency)
    balanceAfter = currency.balanceOf(whale)
    print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/1e18)
    print("Whale profit %: ", "{:.2%}".format(((currency.balanceOf(whale) - whalebefore)/whale_deposit)*12))