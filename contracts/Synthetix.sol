// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import "./Interfaces/synthetix/ISynth.sol";
import "./Interfaces/synthetix/IReadProxy.sol";
import "./Interfaces/synthetix/ISynthetix.sol";
import "./Interfaces/synthetix/IExchanger.sol";
import "./Interfaces/synthetix/IVirtualSynth.sol";
import "./Interfaces/synthetix/IExchangeRates.sol";
import "./Interfaces/synthetix/IAddressResolver.sol";

contract Synthetix {
    // ========== SYNTHETIX CONFIGURATION ==========
    bytes32 public constant sUSD = "sUSD";
    bytes32 public synthCurrencyKey = "sETH";

    // ========== ADDRESS RESOLVER CONFIGURATION ==========
    bytes32 private constant CONTRACT_SYNTHETIX = "Synthetix";
    bytes32 private constant CONTRACT_EXCHANGER = "Exchanger";
    bytes32 private constant CONTRACT_EXCHANGERATES = "ExchangeRates";
    bytes32 private constant CONTRACT_SYNTHSUSD = "ProxyERC20sUSD";
    bytes32 private constant CONTRACT_SYNTHSETH = "ProxyERC20sETH";
    bytes32 private constant CONTRACT_SYNTHSEUR = "ProxyERC20sEUR";
    bytes32 private constant CONTRACT_SYNTHSBTC = "ProxyERC20sBTC";
    bytes32 private constant CONTRACT_SYNTHSLINK = "ProxyERC20sLINK";
    bytes32 internal contractSynth = "ProxyERC20sETH";

    function _initializeSynthetix(bytes32 _synth) internal {
        synthCurrencyKey = _synth;
        if (_synth == "sETH") {
            contractSynth = CONTRACT_SYNTHSETH;
        } else if (_synth == "sBTC") {
            contractSynth = CONTRACT_SYNTHSBTC;
        } else if (_synth == "sEUR") {
            contractSynth = CONTRACT_SYNTHSEUR;
        } else if (_synth == "sLINK") {
            contractSynth = CONTRACT_SYNTHSLINK;
        }
    }

    IReadProxy public constant readProxy =
        IReadProxy(0x4E3b31eB0E5CB73641EE1E65E7dCEFe520bA3ef2);

    function _balanceOfSynth() internal view returns (uint256) {
        return IERC20(address(_synthCoin())).balanceOf(address(this));
    }

    function _balanceOfSUSD() internal view returns (uint256) {
        return IERC20(address(_synthsUSD())).balanceOf(address(this));
    }

    function _synthToSUSD(uint256 _amount) internal view returns (uint256) {
        return _exchangeRates().effectiveValue(synthCurrencyKey, _amount, sUSD);
    }

    function _sUSDToSynth(uint256 _amount) internal view returns (uint256) {
        return _exchangeRates().effectiveValue(sUSD, _amount, synthCurrencyKey);
    }

    function exchangeSynthToSUSD() internal returns (uint256) {
        // swap full balance synth to sUSD
        uint256 synthBalance = _balanceOfSynth();

        if (synthBalance == 0) {
            return 0;
        }

        return _synthetix().exchange(synthCurrencyKey, synthBalance, sUSD);
    }

    function exchangeSUSDToSynth() internal returns (uint256) {
        // swap full balance of sUSD to synth
        uint256 synthBalance = _balanceOfSUSD();

        if (synthBalance == 0) {
            return 0;
        }

        return _synthetix().exchange(sUSD, synthBalance, synthCurrencyKey);
    }

    function _synthCoin() internal view returns (ISynth) {
        return ISynth(resolver().getAddress(contractSynth));
    }

    function _synthsUSD() internal view returns (ISynth) {
        return ISynth(resolver().getAddress(CONTRACT_SYNTHSUSD));
    }

    function resolver() internal view returns (IAddressResolver) {
        return IAddressResolver(readProxy.target());
    }

    function _synthetix() internal view returns (ISynthetix) {
        return ISynthetix(resolver().getAddress(CONTRACT_SYNTHETIX));
    }

    function _exchangeRates() internal view returns (IExchangeRates) {
        return IExchangeRates(resolver().getAddress(CONTRACT_EXCHANGERATES));
    }

    function _exchanger() internal view returns (IExchanger) {
        return IExchanger(resolver().getAddress(CONTRACT_EXCHANGER));
    }
}
