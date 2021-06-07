import pytest
from brownie import config, Contract
from eth_abi import encode_single


@pytest.fixture(scope="session")
def andre(accounts):
    # Andre, giver of tokens, and maker of yield
    yield accounts[0]


@pytest.fixture(scope="session")
def susd_whale(accounts):
    yield accounts.at("0xa5407eae9ba41422680e2e00537571bcc53efbfd", force=True)


@pytest.fixture(scope="session")
def devms(accounts):
    acc = accounts.at("0x846e211e8ba920B353FB717631C015cf04061Cc9", force=True)
    yield acc


@pytest.fixture(scope="session")
def stratms(accounts):
    acc = accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)
    yield acc


@pytest.fixture(scope="session")
def ychad(accounts):
    acc = accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)
    yield acc


@pytest.fixture(scope="session")
def gov(accounts):
    # yearn multis... I mean YFI governance. I swear!
    yield accounts[1]


@pytest.fixture(scope="session")
def rewards(gov):
    yield gov  # TODO: Add rewards contract


@pytest.fixture(scope="session")
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]


@pytest.fixture(scope="session")
def strategist(accounts):
    # You! Our new Strategist!
    yield accounts[3]


@pytest.fixture(scope="session")
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]


@pytest.fixture(scope="session")
def nocoiner(accounts):
    # Has no tokens (DeFi is a ponzi scheme!)
    yield accounts[5]


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def Vault(pm):
    yield pm(config["dependencies"][0]).Vault


@pytest.fixture(scope="function")
def vault(pm, gov, rewards, guardian, currency):
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    yield vault


@pytest.fixture(scope="session")
def currency(susd):
    yield susd


@pytest.fixture(scope="session")
def resolver():
    yield Contract("0x823bE81bbF96BEc0e25CA13170F5AaCb5B79ba83")


@pytest.fixture(scope="session")
def susd(resolver):
    yield Contract(resolver.getAddress(encode_single("bytes32", b"ProxyERC20sUSD")))


@pytest.fixture(scope="function", autouse=True)
def clean(chain):
    print("Taking snapshot...")
    chain.snapshot()
    yield
    print("Reverting to initial state...")
    chain.revert()


@pytest.fixture(
    params=[
        "sETH",
        # "sBTC", # curve contract is old. it requires another interface with int128
        "sEUR",
        "sLINK",
    ],
    scope="session",
)
def synth_symbol(request):
    symbols = {"sETH": b"sETH", "sBTC": b"sBTC", "sEUR": b"sEUR", "sLINK": b"sLINK"}
    yield symbols[request.param]


@pytest.fixture(scope="session")
def proxy_bytes(synth_symbol):
    proxies = {
        b"sETH": b"ProxysETH",
        b"sBTC": b"ProxysBTC",
        b"sEUR": b"ProxysEUR",
        b"sLINK": b"ProxysLINK",
    }
    bytes_contract = encode_single("bytes32", proxies[synth_symbol])
    yield bytes_contract


@pytest.fixture(scope="session")
def synth(resolver, proxy_bytes):
    yield Contract(resolver.getAddress(proxy_bytes))


@pytest.fixture(scope="session")
def yvault(interface, synth_symbol, request):
    yvaults = {
        b"sETH": "0x986b4AFF588a109c09B50A03f42E4110E29D353F",
        b"sBTC": "0x8414Db07a7F743dEbaFb402070AB01a4E0d2E45e",
        b"sEUR": "0x25212Df29073FfFA7A67399AcEfC2dd75a831A1A",
        b"sLINK": "0xf2db9a7c0ACd427A680D640F02d90f6186E71725",
    }
    yield interface.IVaultV2(yvaults[synth_symbol])


@pytest.fixture(scope="session")
def curveToken(interface, synth_symbol):
    curveTokens = {
        b"sETH": "0xA3D87FffcE63B53E0d54fAa1cc983B7eB0b74A9c",
        b"sBTC": "0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3",
        b"sEUR": "0x194eBd173F6cDacE046C53eACcE9B953F28411d1",
        b"sLINK": "0xcee60cFa923170e4f8204AE08B4fA6A3F5656F3a",
    }
    yield interface.ICrvV3(curveTokens[synth_symbol])


@pytest.fixture(scope="session")
def crv_whale(synth_symbol):
    whales = {
        b"sETH": "0x3c0ffff15ea30c35d7a85b85c0782d6c94e1d238",
        b"sBTC": "0x13c1542a468319688b89e323fe9a3be3a90ebb27",  # synthetix curve pool
        b"sEUR": "0x90bb609649e0451e5ad952683d64bd2d1f245840",
        b"sLINK": "0xfd4d8a17df4c27c1dd245d153ccf4499e806c87d",
    }
    yield (whales[synth_symbol])


@pytest.fixture(scope="session")
def curvePool(interface, synth_symbol, request):
    pools = {
        b"sETH": "0xc5424b857f758e906013f3555dad202e4bdb4567",
        b"sBTC": "0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714",
        b"sEUR": "0x0Ce6a5fF5217e38315f87032CF90686C96627CAA",
        b"sLINK": "0xF178C0b5Bb7e7aBF4e12A4838C7b7c5bA2C623c0",
    }
    yield interface.ICurveFi(pools[synth_symbol])


@pytest.fixture(scope="session")
def live_susd_vault(interface):
    yield interface.IVaultV2("0xa5cA62D95D24A4a350983D5B8ac4EB8638887396")


@pytest.fixture(scope="session")
def strategy(strategist, live_susd_vault, Strategy):
    print("Deploying Strategy")
    strategy = strategist.deploy(
        Strategy,
        live_susd_vault,
        "0xc5424b857f758e906013f3555dad202e4bdb4567",
        "0xA3D87FffcE63B53E0d54fAa1cc983B7eB0b74A9c",
        "0x986b4AFF588a109c09B50A03f42E4110E29D353F",
        2,
        False,
        encode_single("bytes32", b"ProxysETH"),
    )
    yield strategy


@pytest.fixture(scope="function")
def cloned_strategy(
    strategist,
    vault,
    strategy,
    curvePool,
    curveToken,
    yvault,
    synth_symbol,
    proxy_bytes,
    gov,
):
    pool_sizes = {
        b"sETH": 2,
        b"sBTC": 3,
        b"sEUR": 2,
        b"sLINK": 2,
    }

    print("Cloning strategy for", pool_sizes[synth_symbol])
    cloned_strategy = strategy.cloneSingleSidedCurve(
        vault,
        curvePool,
        curveToken,
        yvault,
        pool_sizes[synth_symbol],
        False,
        proxy_bytes,
        {"from": strategist},
    ).return_value
    cloned_strategy = Contract.from_abi("Strategy", cloned_strategy, strategy.abi)
    cloned_strategy.updateSlippageProtectionOut(150, {"from": gov})
    vault.addStrategy(cloned_strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    yield cloned_strategy
