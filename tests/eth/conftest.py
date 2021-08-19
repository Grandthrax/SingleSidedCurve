import pytest
from brownie import Contract, ZERO_ADDRESS, Wei

@pytest.fixture
def live_yvweth_032():
    yield Contract("0xa9fE4601811213c340e850ea305481afF02f5b28")


@pytest.fixture
def gov(live_yvweth_032, accounts):
    yield accounts.at(live_yvweth_032.governance(), force=True)


@pytest.fixture
def seth_pool():
    yield Contract("0xc5424B857f758E906013F3555Dad202e4bdB4567")


@pytest.fixture
def seth_crv_token():
    yield Contract("0xA3D87FffcE63B53E0d54fAa1cc983B7eB0b74A9c")


@pytest.fixture
def yvToken_crvSETH():
    yield Contract("0x986b4AFF588a109c09B50A03f42E4110E29D353F")


@pytest.fixture
def old_seth_strategy():
    yield Contract("0xda988eBb26F505246C59Ba26514340B634F9a7a2")


@pytest.fixture
def strategy(Strategy, strategist, live_yvweth_032, seth_pool, seth_crv_token, yvToken_crvSETH):
    yield Strategy.deploy(
        live_yvweth_032,
        Wei("100 ether"),
        3600,
        50,
        seth_pool,
        seth_crv_token,
        yvToken_crvSETH,
        2,
        ZERO_ADDRESS,
        False,
        "ssc_eth_seth",
        {"from": strategist}
    )


@pytest.fixture
def old_seth_strategy():
    yield Contract("0xda988eBb26F505246C59Ba26514340B634F9a7a2")


@pytest.fixture
def steth_pool():
    yield Contract("0xDC24316b9AE028F1497c275EB9192a3Ea0f67022")


@pytest.fixture
def steth_crv_token():
    yield Contract("0x06325440D014e39736583c165C2963BA99fAf14E")


@pytest.fixture
def yvToken_crvSTETH():
    yield Contract("0xdCD90C7f6324cfa40d7169ef80b12031770B4325")


@pytest.fixture
def ste_strategy_clone(strategy, steth_pool, steth_crv_token, yvToken_crvSTETH, strategist):
    cloned_strategy_address = strategy.cloneSingleSidedCurve(
        strategy.vault(),
        strategist,
        Wei("100 ether"),
        3600,
        50,
        steth_pool,
        steth_crv_token,
        yvToken_crvSTETH,
        2,
        ZERO_ADDRESS,
        False,
        "ssc_eth_steth",
        {"from": strategist}
    ).return_value

    yield Contract.from_abi("Strategy", cloned_strategy_address, strategy.abi)


@pytest.fixture
def old_steth_strategy():
    yield Contract("0x2886971eCAF2610236b4869f58cD42c115DFb47A")


@pytest.fixture
def live_yvweth_042():
    yield Contract("0xa258C4606Ca8206D8aA700cE2143D7db854D168c")


@pytest.fixture
def ste_strategy_clone_042(live_yvweth_042, strategy, steth_pool, steth_crv_token, yvToken_crvSTETH, strategist):
    cloned_strategy_address = strategy.cloneSingleSidedCurve(
        live_yvweth_042,
        strategist,
        Wei("100 ether"),
        3600,
        50,
        steth_pool,
        steth_crv_token,
        yvToken_crvSTETH,
        2,
        ZERO_ADDRESS,
        False,
        "ssc_eth_steth",
        {"from": strategist}
    ).return_value

    yield Contract.from_abi("Strategy", cloned_strategy_address, strategy.abi)


@pytest.fixture
def seth_strategy_clone_042(live_yvweth_042, strategy, seth_pool, seth_crv_token, yvToken_crvSETH, strategist):
    cloned_strategy_address = strategy.cloneSingleSidedCurve(
        live_yvweth_042,
        strategist,
        Wei("100 ether"),
        3600,
        50,
        seth_pool,
        seth_crv_token,
        yvToken_crvSETH,
        2,
        ZERO_ADDRESS,
        False,
        "ssc_eth_seth",
        {"from": strategist}
    ).return_value

    yield Contract.from_abi("Strategy", cloned_strategy_address, strategy.abi)


@pytest.fixture
def old_steth_strategy_042():
    yield Contract("0x8c44Cc5c0f5CD2f7f17B9Aca85d456df25a61Ae8")


@pytest.fixture
def old_seth_strategy_042():
    yield Contract("0xCdC3d3A18c9d83Ee6E10E91B48b1fcb5268C97B5")
