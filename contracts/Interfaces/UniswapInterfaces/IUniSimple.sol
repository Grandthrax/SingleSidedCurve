// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.6.12;

interface IUniSimple {
    function getAmountsOut(uint256 amountIn, address[] calldata path)
        external
        view
        returns (uint256[] memory amounts);
}
