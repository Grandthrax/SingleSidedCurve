import pytest
from brownie import Contract, config, network


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
def mim(interface):
    yield interface.ERC20("0x99d8a9c45b2eca8864373a26d1459e3dff1e17f3")


@pytest.fixture
def wbtc(interface):
    # this one is hbtc
    yield interface.ERC20("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")


@pytest.fixture
def tusd(interface):
    # this one is hbtc
    yield interface.ERC20("0x0000000000085d4780B73119b644AE5ecd22b376")


@pytest.fixture
def dai(interface):
    # this one is hbtc
    yield interface.ERC20("0x6b175474e89094c44da98b954eedeac495271d0f")


@pytest.fixture
def hbtc(interface):
    yield interface.ERC20("0x0316EB71485b0Ab14103307bf65a021042c6d380")


@pytest.fixture
def usdt(interface):
    # this one is hbtc
    yield interface.ERC20("0xdAC17F958D2ee523a2206206994597C13D831ec7")


@pytest.fixture
def whale(accounts, web3, currency, chain, wbtc, dai, hbtc):
    network.gas_price("0 gwei")
    network.gas_limit(6700000)

    daiAcc = accounts.at("0xb0Fa2BeEe3Cf36a7Ac7E99B885b48538Ab364853", force=True)

    # big binance7 wallet
    # acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    # big binance8 wallet
    # acc = accounts.at('0x006d0f31a00e1f9c017ab039e9d0ba699433a28c', force=True)
    acc = accounts.at("0xA929022c9107643515F5c777cE9a910F0D1e490C", force=True)
    # big huboi wallet
    hbtcAcc = accounts.at("0x24d48513EAc38449eC7C310A79584F87785f856F", force=True)

    # wbtc account
    wb = accounts.at("0x3dfd23A6c5E8BbcFc9581d2E864a68feb6a076d3", force=True)
    wbtc.transfer(acc, wbtc.balanceOf(wb), {"from": wb})
    dai.transfer(acc, dai.balanceOf(daiAcc), {"from": daiAcc})
    dai.transfer(acc, hbtc.balanceOf(hbtcAcc), {"from": hbtcAcc})

    assert currency.balanceOf(acc) > 0
    assert wbtc.balanceOf(acc) > 0
    assert hbtc.balanceOf(acc) > 0
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
def yvaultv2Bbtc(interface):
    yield interface.IVaultV2("0x8fA3A9ecd9EFb07A8CE90A6eb014CF3c0E3B32Ef")


@pytest.fixture
def yvaultv2Pbtc(interface):
    yield interface.IVaultV2("0x3c5DF3077BcF800640B5DAE8c91106575a4826E6")


@pytest.fixture
def yvaultv2Mim(interface):
    yield interface.IVaultV2("0x2DfB14E32e2F8156ec15a2c21c3A6c053af52Be8")


@pytest.fixture
def yvaultv2Tusd(interface):
    yield interface.IVaultV2("0xf8768814b88281DE4F532a3beEfA5b85B69b9324")


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
def usdnyvault(Vault):
    yield Vault.at("0x3B96d491f067912D18563d56858Ba7d6EC67a6fa")


@pytest.fixture
def yhbtcstrategy(interface):
    yield interface.IStratV1("0xE02363cB1e4E1B77a74fAf38F3Dbb7d0B70F26D7")


@pytest.fixture
def live_wbtc_vault(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at("0xA696a63cc78DfFa1a63E9E50587C197387FF6C7E")
    yield vault


@pytest.fixture
def live_hbtc_vault(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at("0x0F6121fB28C7C42916d663171063c62684598f9F")
    yield vault


@pytest.fixture
def live_mim_vault(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at("0x2807387F1212cB2852aB97cdAa3627dACa5E4661")
    yield vault


@pytest.fixture
def mim_vault(pm, gov, rewards, guardian, mim):
    currency = mim
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian, {"from": gov})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault


@pytest.fixture
def wbtc_vault(pm, gov, rewards, guardian, wbtc):
    currency = wbtc
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian, {"from": gov})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault


@pytest.fixture
def tusd_vault(pm, gov, rewards, guardian, tusd):
    currency = tusd
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian, {"from": gov})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault


@pytest.fixture
def hbtc_vault(pm, gov, rewards, guardian, hbtc):
    currency = hbtc
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian, {"from": gov})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault


# @pytest.fixture
# def live_strategy_wbtc(Strategy):
#    yield Strategy.at('0x04A508664B053E0A08d5386303E649925CBF763c')


@pytest.fixture
def obCRV(interface):
    yield interface.ICrvV3("0x2fE94ea3d5d4a175184081439753DE15AeF9d614")


@pytest.fixture
def bbtcCRV(interface):
    yield interface.ICrvV3("0x410e3E86ef427e30B9235497143881f717d93c2A")


@pytest.fixture
def pbtcCRV(interface):
    yield interface.ICrvV3("0xDE5331AC4B3630f94853Ff322B66407e0D6331E8")


@pytest.fixture
def threecrv(interface):
    yield interface.ICrvV3("0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490")


@pytest.fixture
def zeroaddress():
    yield "0x0000000000000000000000000000000000000000"


@pytest.fixture
def sbtccrv(interface):
    yield interface.ICrvV3("0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3")


@pytest.fixture
def healthcheck(Contract):
    yield Contract("0xDDCea799fF1699e98EDF118e0629A974Df7DF012")


@pytest.fixture
def usdn3crv(interface):
    yield interface.ICrvV3("0x4f3E8F405CF5aFC05D68142F3783bDfE13811522")


@pytest.fixture
def hCRV(interface):
    yield interface.ICrvV3("0xb19059ebb43466C323583928285a49f558E572Fd")


@pytest.fixture
def curvePool(interface):
    yield interface.ICurveFi("0x4CA9b3063Ec5866A4B82E437059D2C43d1be596F")


@pytest.fixture
def depositUsdn(interface):
    yield interface.ICurveFi("0x094d12e5b541784701FD8d65F11fc0598FBC6332")


@pytest.fixture
def curvePoolObtc(interface):
    yield interface.ICurveFi("0xd5BCf53e2C81e1991570f33Fa881c49EEa570C8D")


@pytest.fixture
def curvePoolMim(interface):
    yield interface.ICurveFi("0x5a6A4D54456819380173272A5E8E9B9904BdF41B")


@pytest.fixture
def curvePoolTusd(interface):
    yield interface.ICurveFi("0xEcd5e75AFb02eFa118AF914515D6521aaBd189F1")


@pytest.fixture
def curvePoolBbtc(interface):
    yield interface.ICurveFi("0xC45b2EEe6e09cA176Ca3bB5f7eEe7C47bF93c756")


@pytest.fixture
def curvePoolPbtc(interface):
    yield interface.ICurveFi("0x11F419AdAbbFF8d595E7d5b223eee3863Bb3902C")


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
def dai_vault(pm, gov, rewards, guardian, dai):
    currency = dai
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian, {"from": gov})
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
def live_strategy_wbtc_obt(Strategy):
    strategy = Strategy.at("0x64B2a32f030D9210E51ed8884C0D58b89137Ca81")

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
        "ssc ib3crv",
        {"from": strategist},
    )
    yield Strategy.at(tx.return_value)


@pytest.fixture
def strategy_dai_ib(
    strategist,
    keeper,
    live_vault_dai,
    Strategy,
    ibCurvePool,
    ib3CRV,
    ibyvault,
    healthcheck,
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
        "ssc ib3crv",
    )
    strategy.setHealthCheck(healthcheck)
    strategy.setKeeper(keeper)
    yield strategy


@pytest.fixture
def strategy_dai_usdn(
    strategist, keeper, dai_vault, Strategy, depositUsdn, usdn3crv, usdnyvault, threecrv
):
    strategy = strategist.deploy(
        Strategy,
        dai_vault,
        1_000_000 * 1e18,
        3600,
        5000,
        depositUsdn,
        usdn3crv,
        usdnyvault,
        4,
        threecrv,
        False,
        "ssc ib3crv",
    )
    # strategy.setKeeper(keeper)
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
        "ssc wbtc hbtc",
    )
    strategy.setKeeper(keeper)
    yield strategy


@pytest.fixture
def strategy_wbtc_obtc(
    gov,
    keeper,
    wbtc_vault,
    healthcheck,
    Strategy,
    curvePoolObtc,
    obCRV,
    sbtccrv,
    yvaultv2Obtc,
):
    strategy = gov.deploy(
        Strategy,
        wbtc_vault,
        30 * 1e8,
        3600,
        500,
        curvePoolObtc,
        obCRV,
        yvaultv2Obtc,
        4,
        sbtccrv,
        False,
        "ssc wbtc obtc",
    )
    strategy.setHealthCheck(healthcheck)
    strategy.setKeeper(keeper)
    yield strategy


@pytest.fixture
def live_strategy_mim_mim():
    yield Contract("0x56371B45Cf4ADB082B0B3C49928b9B9e311F223C")


@pytest.fixture
def strategy_mim_mim(
    gov,
    keeper,
    mim_vault,
    healthcheck,
    Strategy,
    curvePoolMim,
    zeroaddress,
    yvaultv2Mim,
):
    strategy = gov.deploy(
        Strategy,
        mim_vault,
        1_000_000 * 1e18,  # max single invest
        3600,  # min time per invest
        10_000,  # slippage protection in
        curvePoolMim,  # curve pool
        curvePoolMim,  # curve token
        yvaultv2Mim,  # yVault
        2,  # pool size
        zeroaddress,  # meta token
        False,  # has underlying
        "ssc mim mim",  # strategy name
    )
    strategy.setHealthCheck(healthcheck)
    strategy.setKeeper(keeper)
    yield strategy


@pytest.fixture
def strategy_tusd_tusd(
    gov,
    keeper,
    tusd_vault,
    healthcheck,
    Strategy,
    curvePoolTusd,
    zeroaddress,
    yvaultv2Tusd,
):
    strategy = gov.deploy(
        Strategy,
        tusd_vault,
        1_000_000 * 1e18,
        3600,
        10_000,
        curvePoolTusd,
        curvePoolTusd,
        yvaultv2Tusd,
        2,
        zeroaddress,
        False,
        "ssc tusd tusd",
    )
    strategy.setHealthCheck(healthcheck)
    strategy.setKeeper(keeper)
    yield strategy


@pytest.fixture
def strategy_dai_ib(
    strategist,
    keeper,
    live_vault_dai,
    Strategy,
    ibCurvePool,
    ib3CRV,
    ibyvault,
    healthcheck,
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
        "ssc ib3crv",
    )
    strategy.setHealthCheck(healthcheck)
    strategy.setKeeper(keeper)
    yield strategy


@pytest.fixture
def live_strategy_wbtc_bbtc(
    gov,
    keeper,
    live_strategy_wbtc_obt,
    live_wbtc_vault,
    healthcheck,
    Strategy,
    curvePoolBbtc,
    bbtcCRV,
    sbtccrv,
    yvaultv2Bbtc,
    accounts,
):
    gov = accounts.at(live_wbtc_vault.governance(), force=True)
    strategist = gov
    tx = live_strategy_wbtc_obt.cloneSingleSidedCurve(
        live_wbtc_vault,
        strategist,
        60 * 1e8,
        360,
        500,
        curvePoolBbtc,
        bbtcCRV,
        yvaultv2Bbtc,
        4,
        sbtccrv,
        False,
        "ssc wbtc bbtc",
        {"from": strategist},
    )
    strategy = Strategy.at(tx.return_value)
    strategy.setHealthCheck(healthcheck, {"from": gov})
    yield strategy


@pytest.fixture
def live_strategy_wbtc_pbtc(
    gov,
    keeper,
    live_strategy_wbtc_obt,
    live_wbtc_vault,
    healthcheck,
    Strategy,
    curvePoolPbtc,
    pbtcCRV,
    sbtccrv,
    yvaultv2Pbtc,
    accounts,
):
    gov = accounts.at(live_wbtc_vault.governance(), force=True)
    strategist = gov
    tx = live_strategy_wbtc_obt.cloneSingleSidedCurve(
        live_wbtc_vault,
        strategist,
        60 * 1e8,
        360,
        500,
        curvePoolPbtc,
        pbtcCRV,
        yvaultv2Pbtc,
        4,
        sbtccrv,
        False,
        "ssc wbtc pbtc",
        {"from": strategist},
    )
    strategy = Strategy.at(tx.return_value)
    strategy.setHealthCheck(healthcheck, {"from": gov})
    yield strategy


@pytest.fixture
def live_strategy_wbtc_obtc(
    gov,
    keeper,
    live_wbtc_vault,
    healthcheck,
    Strategy,
    curvePoolObtc,
    obCRV,
    sbtccrv,
    yvaultv2Obtc,
    accounts,
):
    gov = accounts.at(live_wbtc_vault.governance(), force=True)
    strategy = gov.deploy(
        Strategy,
        live_wbtc_vault,
        60 * 1e8,
        360,
        500,
        curvePoolObtc,
        obCRV,
        yvaultv2Obtc,
        4,
        sbtccrv,
        False,
        "ssc wbtc obtc",
    )
    strategy.setHealthCheck(healthcheck, {"from": gov})
    yield strategy


@pytest.fixture
def strategy_hbtc_hbtc(
    gov, keeper, hbtc_vault, Strategy, curvePool, hCRV, yvaultv2, zeroaddress
):
    strategy = gov.deploy(
        Strategy,
        hbtc_vault,
        30 * 1e18,
        3600,
        500,
        curvePool,
        hCRV,
        yvaultv2,
        2,
        zeroaddress,
        False,
        "ssc hbtc hbtc",
    )

    yield strategy


@pytest.fixture
def strategy_hbtc_hbtc_live(Strategy):
    strategy = Strategy.at("0x3F64bb4C334488765A82a697cb210DA9BB876B67")

    yield strategy


@pytest.fixture
def clonedstrategy_hbtc_hbtc(
    strategist,
    strategy_hbtc_hbtc,
    keeper,
    hbtc_vault,
    Strategy,
    curvePool,
    hCRV,
    yvaultv2,
    zeroaddress,
):
    strategy = strategy_hbtc_hbtc
    tx = strategy.cloneSingleSidedCurve(
        hbtc_vault,
        strategist,
        30 * 1e18,
        3600,
        500,
        curvePool,
        hCRV,
        yvaultv2,
        2,
        zeroaddress,
        False,
        "ssc hbtc hbtc",
    )
    new_strategy = Strategy.at(tx.return_value)

    yield new_strategy


@pytest.fixture
def clonedstrategy_hbtc_hbtc(
    strategist,
    strategy_hbtc_hbtc,
    keeper,
    hbtc_vault,
    Strategy,
    curvePool,
    hCRV,
    yvaultv2,
    zeroaddress,
):
    strategy = strategy_hbtc_hbtc
    tx = strategy.cloneSingleSidedCurve(
        hbtc_vault,
        strategist,
        30 * 1e18,
        3600,
        500,
        curvePool,
        hCRV,
        yvaultv2,
        2,
        zeroaddress,
        False,
        "ssc hbtc hbtc",
    )
    new_strategy = Strategy.at(tx.return_value)

    yield new_strategy


@pytest.fixture
def strategy(strategist, keeper, vault, Strategy):
    strategy = strategist.deploy(Strategy, vault, 2 * 1e18)
    strategy.setKeeper(keeper)
    yield strategy


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
