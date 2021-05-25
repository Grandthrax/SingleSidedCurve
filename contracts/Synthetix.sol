// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import "./Interfaces/synthetix/ISynth.sol";
import "./Interfaces/synthetix/IReadProxy.sol";
import "./Interfaces/synthetix/ISynthetix.sol";
import "./Interfaces/synthetix/IExchanger.sol";
import "./Interfaces/synthetix/IVirtualSynth.sol";
import "./Interfaces/synthetix/IExchangeRates.sol";
import "./Interfaces/synthetix/IAddressResolver.sol";

contract Synthetix {
    using SafeMath for uint256;
    // ========== SYNTHETIX CONFIGURATION ==========
    bytes32 public constant sUSD = "sUSD";
    bytes32 public synthCurrencyKey;

    bytes32 internal constant TRACKING_CODE =
        "0x594541524e000000000000000000000000000000000000000000000000000000";

    // ========== ADDRESS RESOLVER CONFIGURATION ==========
    bytes32 private constant CONTRACT_SYNTHETIX = "Synthetix";
    bytes32 private constant CONTRACT_EXCHANGER = "Exchanger";
    bytes32 private constant CONTRACT_EXCHANGERATES = "ExchangeRates";
    bytes32 private constant CONTRACT_SYNTHSUSD = "ProxyERC20sUSD";

    IReadProxy public constant readProxy =
        IReadProxy(0x4E3b31eB0E5CB73641EE1E65E7dCEFe520bA3ef2);

    function _initializeSynthetix(bytes32 _synth) internal {
        // sETH / sBTC / sEUR / sLINK
        synthCurrencyKey = _synth;
    }

    function _balanceOfSynth() internal view returns (uint256) {
        return IERC20(address(_synthCoin())).balanceOf(address(this));
    }

    function _balanceOfSUSD() internal view returns (uint256) {
        return IERC20(address(_synthsUSD())).balanceOf(address(this));
    }

    function _synthToSUSD(uint256 _amountToSend)
        internal
        view
        returns (uint256 amountReceived)
    {
        (amountReceived, , ) = _exchanger().getAmountsForExchange(
            _amountToSend,
            synthCurrencyKey,
            sUSD
        );
    }

    function _sUSDToSynth(uint256 _amountToSend)
        internal
        view
        returns (uint256 amountReceived)
    {
        (amountReceived, , ) = _exchanger().getAmountsForExchange(
            _amountToSend,
            sUSD,
            synthCurrencyKey
        );
    }

    function _sUSDFromSynth(uint256 _amountToReceive)
        internal
        view
        returns (uint256 amountToSend)
    {
        // NOTE: the fee of the trade that would be done (sUSD => synth) in this case
        uint256 feeRate =
            _exchanger().feeRateForExchange(sUSD, synthCurrencyKey); // in base 1e18
        // formula => amountToReceive (Synth) * price (sUSD/Synth) / (1 - feeRate)
        return
            _exchangeRates()
                .effectiveValue(synthCurrencyKey, _amountToReceive, sUSD)
                .mul(1e18)
                .div(uint256(1e18).sub(feeRate));
    }

    function _synthFromSUSD(uint256 _amountToReceive)
        internal
        view
        returns (uint256 amountToSend)
    {
        // NOTE: the fee of the trade that would be done (synth => sUSD) in this case
        uint256 feeRate =
            _exchanger().feeRateForExchange(synthCurrencyKey, sUSD); // in base 1e18
        // formula => amountToReceive (sUSD) * price (Synth/sUSD) / (1 - feeRate)
        return
            _exchangeRates()
                .effectiveValue(sUSD, _amountToReceive, synthCurrencyKey)
                .mul(1e18)
                .div(uint256(1e18).sub(feeRate));
    }

    function exchangeSynthToSUSD() internal returns (uint256) {
        // swap full balance synth to sUSD
        uint256 synthBalance = _balanceOfSynth();

        if (synthBalance == 0) {
            return 0;
        }

        return
            _synthetix().exchangeWithTracking(
                synthCurrencyKey,
                synthBalance,
                sUSD,
                address(this),
                TRACKING_CODE
            );
    }

    function exchangeSUSDToSynth(uint256 amount) internal returns (uint256) {
        // swap amount of sUSD for Synth
        if (amount == 0) {
            return 0;
        }

        return
            _synthetix().exchangeWithTracking(
                sUSD,
                amount,
                synthCurrencyKey,
                address(this),
                TRACKING_CODE
            );
    }

    function resolver() internal view returns (IAddressResolver) {
        return IAddressResolver(readProxy.target());
    }

    function _synthCoin() internal view returns (ISynth) {
        return ISynth(resolver().getSynth(synthCurrencyKey));
    }

    function _synthsUSD() internal view returns (ISynth) {
        return ISynth(resolver().getAddress(CONTRACT_SYNTHSUSD));
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
