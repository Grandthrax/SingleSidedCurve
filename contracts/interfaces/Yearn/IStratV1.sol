// SPDX-License-Identifier: MIT

pragma solidity 0.6.12;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IStratV1 is IERC20 {
    function earn() external;

    function harvest() external;

}
