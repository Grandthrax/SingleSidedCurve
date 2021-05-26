import pytest
from brownie import config


@pytest.fixture
def andre(accounts):
    # Andre, giver of tokens, and maker of yield
    yield accounts[0]


@pytest.fixture
def currency(interface, usdt):
    # this one is hbtc
    # yield interface.ERC20('0x0316EB71485b0Ab14103307bf65a021042c6d380')
    yield usdt


@pytest.fixture
def live_vault_usdt(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at("0x32651dD149a6EC22734882F790cBEB21402663F9")
    yield vault


@pytest.fixture
def live_vault_dai(interface):
    vault = interface.IVaultV2("0x19D3364A399d251E894aC732651be8B0E4e85001")
    yield vault


@pytest.fixture
def wbtc(interface):
    # this one is hbtc
    yield interface.ERC20("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")


@pytest.fixture
def dai(interface):
    # this one is hbtc
    yield interface.ERC20("0x6b175474e89094c44da98b954eedeac495271d0f")


@pytest.fixture
def usdt(interface):
    # this one is hbtc
    yield interface.ERC20("0xdAC17F958D2ee523a2206206994597C13D831ec7")


@pytest.fixture
def whale(accounts, web3, currency, chain, wbtc, dai):

    daiAcc = accounts.at("0xb0Fa2BeEe3Cf36a7Ac7E99B885b48538Ab364853", force=True)

    # big binance7 wallet
    # acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    # big binance8 wallet
    # acc = accounts.at('0x006d0f31a00e1f9c017ab039e9d0ba699433a28c', force=True)
    acc = accounts.at("0xA929022c9107643515F5c777cE9a910F0D1e490C", force=True)
    # big huboi wallet
    # acc = accounts.at('0x24d48513EAc38449eC7C310A79584F87785f856F', force=True)

    # wbtc account
    wb = accounts.at("0x3dfd23A6c5E8BbcFc9581d2E864a68feb6a076d3", force=True)
    wbtc.transfer(acc, wbtc.balanceOf(wb), {"from": wb})
    dai.transfer(acc, dai.balanceOf(daiAcc), {"from": daiAcc})

    assert currency.balanceOf(acc) > 0
    assert wbtc.balanceOf(acc) > 0
    yield acc


@pytest.fixture
def yvault(interface):
    yield interface.IVaultV1("0x46AFc2dfBd1ea0c0760CAD8262A5838e803A37e5")


@pytest.fixture
def yvaultv2(interface):
    yield interface.IVaultV2("0x625b7DF2fa8aBe21B0A976736CDa4775523aeD1E")


@pytest.fixture
def yvaultv2Obtc(interface):
    yield interface.IVaultV2("0xe9Dc63083c464d6EDcCFf23444fF3CFc6886f6FB")


@pytest.fixture
def yhbtcstrategyv2(Strategy):
    yield Strategy.at("0x91cBf0014a966615e1050c90A1aBf1d1d5d8cffd")


@pytest.fixture
def wbtcstrategynew(Strategy):
    yield Strategy.at("0xb85413f6d07454828eAc7E62df7d847316475178")


@pytest.fixture
def ibyvault(Vault):
    yield Vault.at("0x27b7b1ad7288079A66d12350c828D3C00A6F07d7")


@pytest.fixture
def yhbtcstrategy(interface):
    yield interface.IStratV1("0xE02363cB1e4E1B77a74fAf38F3Dbb7d0B70F26D7")


@pytest.fixture
def live_wbtc_vault(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at("0xA696a63cc78DfFa1a63E9E50587C197387FF6C7E")
    yield vault


# @pytest.fixture
# def live_strategy_wbtc(Strategy):
#    yield Strategy.at('0x04A508664B053E0A08d5386303E649925CBF763c')


@pytest.fixture
def obCRV(interface):
    yield interface.ICrvV3("0x2fE94ea3d5d4a175184081439753DE15AeF9d614")


@pytest.fixture
def hCRV(interface):
    yield interface.ICrvV3("0xb19059ebb43466C323583928285a49f558E572Fd")


@pytest.fixture
def curvePool(interface):
    yield interface.ICurveFi("0x4CA9b3063Ec5866A4B82E437059D2C43d1be596F")


@pytest.fixture
def curvePoolObtc(interface):
    yield interface.ICurveFi("0xd81dA8D904b52208541Bade1bD6595D8a251F8dd")


@pytest.fixture
def ibCurvePool(interface):
    yield interface.ICurveFi("0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF")


@pytest.fixture
def ib3CRV(interface):
    yield interface.ICrvV3("0x5282a4eF67D9C33135340fB3289cc1711c13638C")


@pytest.fixture
def devms(accounts):
    acc = accounts.at("0x846e211e8ba920B353FB717631C015cf04061Cc9", force=True)
    yield acc


@pytest.fixture
def stratms(accounts):
    acc = accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)
    yield acc


@pytest.fixture
def orb(accounts):
    acc = accounts.at("0x710295b5f326c2e47e6dd2e7f6b5b0f7c5ac2f24", force=True)
    yield acc


@pytest.fixture
def ychad(accounts):
    acc = accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)
    yield acc


@pytest.fixture
def samdev(accounts):
    # big binance7 wallet
    # acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    # big binance8 wallet
    acc = accounts.at("0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0", force=True)

    yield acc


@pytest.fixture
def token(andre, Token):
    yield andre.deploy(Token)


@pytest.fixture
def gov(accounts):
    # yearn multis... I mean YFI governance. I swear!
    yield accounts[1]


@pytest.fixture
def rewards(gov):
    yield gov  # TODO: Add rewards contract


@pytest.fixture
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]


@pytest.fixture
def Vault(pm):
    yield pm(config["dependencies"][0]).Vault


@pytest.fixture
def vault(pm, gov, rewards, guardian, currency):
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault


@pytest.fixture
def wbtc_vault(pm, gov, rewards, guardian, wbtc):
    currency = wbtc
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault


@pytest.fixture
def strategist(accounts):
    # You! Our new Strategist!
    yield accounts[3]


@pytest.fixture
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]


@pytest.fixture
def live_strategy(Strategy):
    strategy = Strategy.at("0xCa8C5e51e235EF1018B2488e4e78e9205064D736")

    yield strategy


@pytest.fixture
def live_strategy_usdt(Strategy):
    strategy = Strategy.at("0xf840d061E83025F4cD6610AE5DDebCcA43327f9f")

    yield strategy


@pytest.fixture
def live_strategy_wbtc(Strategy):
    strategy = Strategy.at("0x40b04B3ed9845B8Be200Aa2D9C3eDC2bE0a5f01f")

    yield strategy


@pytest.fixture
def live_vault(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at("0xdCD90C7f6324cfa40d7169ef80b12031770B4325")
    yield vault


@pytest.fixture
def live_usdt_vault(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at("0x7Da96a3891Add058AdA2E826306D812C638D87a7")
    yield vault


@pytest.fixture
def strategy_usdt_ib(
    strategist,
    Strategy,
    keeper,
    live_usdt_vault,
    live_strategy_wbtc,
    ibCurvePool,
    ib3CRV,
    ibyvault,
):
    # strategy = strategist.deploy(Strategy, live_usdt_vault, 500_000*1e6, 3600, 500, ibCurvePool, ib3CRV, ibyvault,3, True)
    tx = live_strategy_wbtc.cloneSingleSidedCurve(
        live_usdt_vault,
        strategist,
        strategist,
        strategist,
        500_000 * 1e6,
        3600,
        500,
        ibCurvePool,
        ib3CRV,
        ibyvault,
        3,
        True,
        {"from": strategist},
    )
    yield Strategy.at(tx.return_value)


@pytest.fixture
def strategy_dai_ib(
    strategist, keeper, live_vault_dai, Strategy, ibCurvePool, ib3CRV, ibyvault
):
    strategy = strategist.deploy(
        Strategy,
        live_vault_dai,
        1_000_000 * 1e18,
        3600,
        500,
        ibCurvePool,
        ib3CRV,
        ibyvault,
        3,
        True,
    )
    strategy.setKeeper(keeper)
    yield strategy


@pytest.fixture
def strategy_wbtc_hbtc(
    strategist, keeper, live_wbtc_vault, Strategy, curvePool, hCRV, yvaultv2
):
    strategy = strategist.deploy(
        Strategy,
        live_wbtc_vault,
        30 * 1e8,
        3600,
        500,
        curvePool,
        hCRV,
        yvaultv2,
        2,
        False,
    )
    strategy.setKeeper(keeper)
    yield strategy


@pytest.fixture
def strategy_wbtc_obtc(
    strategist, keeper, live_wbtc_vault, Strategy, curvePoolObtc, obCRV, yvaultv2Obtc
):
    strategy = strategist.deploy(
        Strategy,
        live_wbtc_vault,
        30 * 1e8,
        3600,
        500,
        curvePoolObtc,
        obCRV,
        yvaultv2Obtc,
        4,
        False,
    )
    strategy.setKeeper(keeper)
    yield strategy


@pytest.fixture
def strategy(strategist, keeper, vault, Strategy):
    strategy = strategist.deploy(Strategy, vault, 2 * 1e18)
    strategy.setKeeper(keeper)
    yield strategy


@pytest.fixture
def zapper(strategist, ZapSteth):
    zapper = strategist.deploy(ZapSteth)
    yield zapper


@pytest.fixture
def nocoiner(accounts):
    # Has no tokens (DeFi is a ponzi scheme!)
    yield accounts[5]


@pytest.fixture
def pleb(accounts, andre, token, vault):
    # Small fish in a big pond
    a = accounts[6]
    # Has 0.01% of tokens (heard about this new DeFi thing!)
    bal = token.totalSupply() // 10000
    token.transfer(a, bal, {"from": andre})
    # Unlimited Approvals
    token.approve(vault, 2 ** 256 - 1, {"from": a})
    # Deposit half their stack
    vault.deposit(bal // 2, {"from": a})
    yield a


@pytest.fixture
def chad(accounts, andre, token, vault):
    # Just here to have fun!
    a = accounts[7]
    # Has 0.1% of tokens (somehow makes money trying every new thing)
    bal = token.totalSupply() // 1000
    token.transfer(a, bal, {"from": andre})
    # Unlimited Approvals
    token.approve(vault, 2 ** 256 - 1, {"from": a})
    # Deposit half their stack
    vault.deposit(bal // 2, {"from": a})
    yield a


@pytest.fixture
def greyhat(accounts, andre, token, vault):
    # Chaotic evil, will eat you alive
    a = accounts[8]
    # Has 1% of tokens (earned them the *hard way*)
    bal = token.totalSupply() // 100
    token.transfer(a, bal, {"from": andre})
    # Unlimited Approvals
    token.approve(vault, 2 ** 256 - 1, {"from": a})
    # Deposit half their stack
    vault.deposit(bal // 2, {"from": a})
    yield a
