// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "./interfaces/curve/Curve.sol";
import "./interfaces/curve/ICrvV3.sol";
import "./interfaces/erc20/IERC20Extended.sol";

// These are the core Yearn libraries
import "@yearnvaults/contracts/BaseStrategy.sol";


import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";

interface IUni {
    function getAmountsOut(uint256 amountIn, address[] calldata path) external view returns (uint256[] memory amounts);
}



// Import interfaces for many popular DeFi projects, or add your own!
//import "../interfaces/<protocol>/<Interface>.sol";

contract StrategySusdv2 is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    ICurveFi public curvePool;// =  ICurveFi(address(0x4CA9b3063Ec5866A4B82E437059D2C43d1be596F));
    Zap public zapOut;
    ICurveFi public basePool;
    ICrvV3 public curveToken;// = ICrvV3(address(0xb19059ebb43466C323583928285a49f558E572Fd));

    address public constant weth = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public constant uniswapRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;

    VaultAPI public yvToken;// = IVaultV1(address(0x46AFc2dfBd1ea0c0760CAD8262A5838e803A37e5));
    //IERC20Extended public middleToken; // the token between bluechip and curve pool

    uint256 public lastInvest;
    uint256 public minTimePerInvest;// = 3600;
    uint256 public maxSingleInvest;// // 2 hbtc per hour default
    uint256 public slippageProtectionIn;// = 50; //out of 10000. 50 = 0.5%
    uint256 public slippageProtectionOut;// = 50; //out of 10000. 50 = 0.5%
    uint256 public constant DENOMINATOR = 10_000;

    uint8 private want_decimals;
    uint8 private middle_decimals;

    int128 public curveId;
    uint256 public poolSize;
    bool public hasUnderlying;
    address public metaToken;

    bool public withdrawProtection;

    constructor(
        address _vault,
        uint256 _maxSingleInvest,
        uint256 _minTimePerInvest,
        uint256 _slippageProtectionIn,
        address _curvePool,
        address _zapOut,
        address _curveToken,
        address _yvToken,
        uint256 _poolSize,
        address _metaToken,
        bool _hasUnderlying
    ) public BaseStrategy(_vault) {
         _initializeStrat(_maxSingleInvest, _minTimePerInvest, _slippageProtectionIn, _curvePool, _zapOut, _curveToken, _yvToken, _poolSize, _metaToken, _hasUnderlying);
    }

    function initialize(
        address _vault,
        address _strategist,
        uint256 _maxSingleInvest,
        uint256 _minTimePerInvest,
        uint256 _slippageProtectionIn,
        address _curvePool,
        address _zapOut,
        address _curveToken,
        address _yvToken,
        uint256 _poolSize,
        address _metaToken,
        bool _hasUnderlying
    ) external {
        //note: initialise can only be called once. in _initialize in BaseStrategy we have: require(address(want) == address(0), "Strategy already initialized");
        _initialize(_vault, _strategist, _strategist, _strategist);
        _initializeStrat(_maxSingleInvest, _minTimePerInvest, _slippageProtectionIn, _curvePool, _zapOut, _curveToken, _yvToken, _poolSize, _metaToken, _hasUnderlying);
    }

    function _initializeStrat(
        uint256 _maxSingleInvest,
        uint256 _minTimePerInvest,
        uint256 _slippageProtectionIn,
        address _curvePool,
        address _zapOut,
        address _curveToken,
        address _yvToken,
        uint256 _poolSize,
        address _metaToken,
        bool _hasUnderlying
    ) internal {
        require(want_decimals == 0, "Already Initialized");
        require(_poolSize > 1 && _poolSize < 5, "incorrect pool size");

        curvePool = ICurveFi(_curvePool);
        zapOut = Zap(_zapOut);

        if(_metaToken != address(0)) {
            basePool = ICurveFi(curvePool.pool());
            metaToken = _metaToken;

            for(uint i = 0; i < _poolSize; i++){
                if( i == 0){
                    if(curvePool.coins(0) == address(want)){
                        require(false, "ONLY USE META FOR BASE");
                    }
                }else{
                    if(curvePool.base_coins(i-1) == address(want)){
                        curveId = int128(i);
                        break;
                    }
                }
                if(i == _poolSize - 1){ // doesnt matter if it overflows
                    require(false, "incorrect want for curve pool");
                }
            }

        } else {
            basePool = ICurveFi(_curvePool);

            if(curvePool.coins(0) == address(want) || (_hasUnderlying && curvePool.underlying_coins(0) == address(want) )){
                curveId = 0;
            }else if ( curvePool.coins(1) == address(want) || (_hasUnderlying && curvePool.underlying_coins(1) == address(want) )){
                curveId = 1;
            }else if ( curvePool.coins(2) == address(want) || (_hasUnderlying && curvePool.underlying_coins(2) == address(want) )){
                curveId = 2;
            }else if ( curvePool.coins(3) == address(want) || (_hasUnderlying && curvePool.underlying_coins(3) == address(want) )){
                //will revert if there are not enough coins
            curveId = 3;
            }else{
                require(false, "incorrect want for curve pool");
            }
        }

        maxSingleInvest = _maxSingleInvest;
        minTimePerInvest = _minTimePerInvest;
        slippageProtectionIn = _slippageProtectionIn;
        slippageProtectionOut = _slippageProtectionIn; // use In to start with to save on stack

        poolSize = _poolSize;
        hasUnderlying = _hasUnderlying;

        yvToken = VaultAPI(_yvToken);
        curveToken = ICrvV3(_curveToken);

        _setupStatics();

    }
    function _setupStatics() internal {
        maxReportDelay = 86400;
        profitFactor = 1500;
        minReportDelay = 3600;
        debtThreshold = 100*1e18;
        withdrawProtection = true;
        want_decimals = IERC20Extended(address(want)).decimals();

        want.safeApprove(address(curvePool), uint256(-1));
        curveToken.approve(address(zapOut), uint256(-1));

        //deposit contract needs permissions
        if(metaToken != address(0)){
            IERC20(metaToken).safeApprove(address(curvePool), uint256(-1)); // 3crv
            curveToken.approve(address(curvePool), uint256(-1));
        }
        curveToken.approve(address(yvToken), uint256(-1));
    }

    event Cloned(address indexed clone);
    function cloneSingleSidedCurve(
        address _vault,
        address _strategist,
        uint256 _maxSingleInvest,
        uint256 _minTimePerInvest,
        uint256 _slippageProtectionIn,
        address _curvePool,
        address _zapOut,
        address _curveToken,
        address _yvToken,
        uint256 _poolSize,
        address _metaToken,
        bool _hasUnderlying
    ) external returns (address newStrategy){
         bytes20 addressBytes = bytes20(address(this));

        assembly {
            // EIP-1167 bytecode
            let clone_code := mload(0x40)
            mstore(clone_code, 0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000000000000000000000)
            mstore(add(clone_code, 0x14), addressBytes)
            mstore(add(clone_code, 0x28), 0x5af43d82803e903d91602b57fd5bf30000000000000000000000000000000000)
            newStrategy := create(0, clone_code, 0x37)
        }

        StrategySusdv2(newStrategy).initialize(_vault, _strategist, _maxSingleInvest, _minTimePerInvest, _slippageProtectionIn, _curvePool, _zapOut, _curveToken, _yvToken, _poolSize, _metaToken, _hasUnderlying);

        emit Cloned(newStrategy);

    }


    function name() external override view returns (string memory) {
        return string(abi.encodePacked("SingleSidedCrv", IERC20Extended(address(want)).symbol()));
    }

    function updateMinTimePerInvest(uint256 _minTimePerInvest) public onlyAuthorized {
        minTimePerInvest = _minTimePerInvest;
    }
    function updateMaxSingleInvest(uint256 _maxSingleInvest) public onlyAuthorized {
        maxSingleInvest = _maxSingleInvest;
    }
    function updateSlippageProtectionIn(uint256 _slippageProtectionIn) public onlyAuthorized {
        slippageProtectionIn = _slippageProtectionIn;
    }
    function updateSlippageProtectionOut(uint256 _slippageProtectionOut) public onlyAuthorized {
        slippageProtectionOut = _slippageProtectionOut;
    }

    function delegatedAssets() public override view returns (uint256) {
        return vault.strategies(address(this)).totalDebt;
    }

    function estimatedTotalAssets() public override view returns (uint256) {
        uint256 totalCurveTokens = curveTokensInYVault().add(curveToken.balanceOf(address(this)));
        return want.balanceOf(address(this)).add(curveTokenToWant(totalCurveTokens));
    }

    // returns value of total
    function curveTokenToWant(uint256 tokens) public view returns (uint256) {
        if(tokens == 0){
            return 0;
        }

        uint256 virtualOut = virtualPriceToWant().mul(tokens).div(1e18);

        return virtualOut;
    }

    //we lose some precision here. but it shouldnt matter as we are underestimating
    function virtualPriceToWant() public view returns (uint256) {

        uint256 virtualPrice = basePool.get_virtual_price();
        /*if(metaToken){
            //warning: base virtual price is not cached and not live
            virtualPrice = virtualPrice.mul(basePool.base_virtual_price()).div(1e18);
        }*/

        if(want_decimals < 18){
            return virtualPrice.div(10 ** (uint256(uint8(18) - want_decimals)));
        }else{
            return virtualPrice;
        }

    }
    /*function virtualPriceToMiddle() public view returns (uint256) {
        if(middle_decimals < 18){
            return curvePool.get_virtual_price().div(10 ** (uint256(uint8(18) - middle_decimals)));
        }else{
            return curvePool.get_virtual_price();
        }

    }*/

    function curveTokensInYVault() public view returns (uint256) {
        uint256 balance = yvToken.balanceOf(address(this));

        if(yvToken.totalSupply() == 0){
            //needed because of revert on priceperfullshare if 0
            return 0;
        }
        uint256 pricePerShare = yvToken.pricePerShare();
        //curve tokens are 1e18 decimals
        return balance.mul(pricePerShare).div(1e18);
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {

        _debtPayment = _debtOutstanding;

        uint256 debt = vault.strategies(address(this)).totalDebt;
        uint256 currentValue = estimatedTotalAssets();
        uint256 wantBalance = want.balanceOf(address(this));


        if(debt < currentValue){
            //profit
            _profit = currentValue.sub(debt);
        }else{
            _loss = debt.sub(currentValue);
        }

        uint256 toFree = _debtPayment.add(_profit);

        if(toFree > wantBalance){
            toFree = toFree.sub(wantBalance);

            (, uint256 withdrawalLoss) = withdrawSome(toFree);

            //when we withdraw we can lose money in the withdrawal
            if(withdrawalLoss < _profit){
                _profit = _profit.sub(withdrawalLoss);

            }else{
                _loss = _loss.add(withdrawalLoss.sub(_profit));
                _profit = 0;
            }

            wantBalance = want.balanceOf(address(this));

            if(wantBalance < _profit){
                _profit = wantBalance;
                _debtPayment = 0;
            }else if (wantBalance < _debtPayment.add(_profit)){
                _debtPayment = wantBalance.sub(_profit);
            }
        }

        /*if(doHealthCheck && debt > 0){
            //set to 10_000 to let any profit through
            if(profitLimitRatio < DENOMINATOR){
                require(_profit < debt.mul(profitLimitRatio).div(DENOMINATOR), "PROFIT TOO HIGH");
            }
            require(_loss < debt.mul(lossLimitRatio).div(DENOMINATOR), "LOSS TOO HIGH");

        }*/

    }

    function liquidateAllPositions() internal override returns (uint256 _amountFreed) {

        (_amountFreed, ) = liquidatePosition(1e36); //we can request a lot. dont use max because of overflow
    }

    function ethToWant(uint256 _amount) public override view returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = weth;
        path[1] = address(want);

        uint256[] memory amounts = IUni(uniswapRouter).getAmountsOut(_amount, path);

        return amounts[amounts.length - 1];
    }

    function tendTrigger(uint256 callCost) public override view returns (bool) {

        uint256 wantBal = want.balanceOf(address(this));
        uint256 _wantToInvest = Math.min(wantBal, maxSingleInvest);

        if(lastInvest.add(minTimePerInvest) < block.timestamp &&  _wantToInvest > 1 && _checkSlip(_wantToInvest)){
            //return true;
        }
    }

    function _checkSlip(uint256 _wantToInvest) public view returns (bool){
        return true;
    }


    function adjustPosition(uint256 _debtOutstanding) internal override {

        if(lastInvest.add(minTimePerInvest) > block.timestamp ){
            return;
        }

        // Invest the rest of the want
        uint256 _wantToInvest = Math.min(want.balanceOf(address(this)), maxSingleInvest);

        if (_wantToInvest > 0) {
            //add to curve (single sided)
            if(_checkSlip(_wantToInvest)){

                uint256 expectedOut = _wantToInvest.mul(1e18).div(virtualPriceToWant());

                uint256 maxSlip = expectedOut.mul(DENOMINATOR.sub(slippageProtectionIn)).div(DENOMINATOR);

                //pool size cannot be more than 4 or less than 2
                if(poolSize == 2){
                    uint256[2] memory amounts;
                    amounts[uint256(curveId)] = _wantToInvest;
                    if(hasUnderlying){
                        curvePool.add_liquidity(amounts, maxSlip, true);
                    }else{
                        curvePool.add_liquidity(amounts, maxSlip);
                    }

                }else if (poolSize == 3){
                    uint256[3] memory amounts;
                    amounts[uint256(curveId)] = _wantToInvest;
                    if(hasUnderlying){
                        curvePool.add_liquidity(amounts, maxSlip, true);
                    }else{
                        curvePool.add_liquidity(amounts, maxSlip);
                    }

                }else{
                    uint256[4] memory amounts;
                    amounts[uint256(curveId)] = _wantToInvest;
                    if(hasUnderlying){
                        curvePool.add_liquidity(amounts, maxSlip, true);
                    }else{
                        curvePool.add_liquidity(amounts, maxSlip);
                    }

                }
                //now add to yearn
                yvToken.deposit();

                lastInvest = block.timestamp;
            }else{
                require(false, "quee");
            }
        }
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {

        uint256 wantBal = want.balanceOf(address(this));
        if(wantBal < _amountNeeded){
            (_liquidatedAmount, _loss) = withdrawSome(_amountNeeded.sub(wantBal));
        }

        _liquidatedAmount = Math.min(_amountNeeded, _liquidatedAmount.add(wantBal));

    }

    //safe to enter more than we have
    function withdrawSome(uint256 _amount) internal returns (uint256 _liquidatedAmount, uint256 _loss) {

        uint256 wantBalanceBefore = want.balanceOf(address(this));

        //let's take the amount we need if virtual price is real. Let's add the
        uint256 virtualPrice = virtualPriceToWant();
        uint256 amountWeNeedFromVirtualPrice = _amount.mul(1e18).div(virtualPrice);

        uint256 crvBeforeBalance = curveToken.balanceOf(address(this)); //should be zero but just incase...

        uint256 pricePerFullShare = yvToken.pricePerShare();
        uint256 amountFromVault = amountWeNeedFromVirtualPrice.mul(1e18).div(pricePerFullShare);

        uint256 yBalance =  yvToken.balanceOf(address(this));


        if(amountFromVault > yBalance){

            amountFromVault = yBalance;
            //this is not loss. so we amend amount

            uint256 _amountOfCrv = amountFromVault.mul(pricePerFullShare).div(1e18);
            _amount = _amountOfCrv.mul(virtualPrice).div(1e18);
        }

        yvToken.withdraw(amountFromVault);
        if(withdrawProtection){
            //this tests that we liquidated all of the expected ytokens. Without it if we get back less then will mark it is loss
            require(yBalance.sub(yvToken.balanceOf(address(this))) >= amountFromVault.sub(1), "YVAULTWITHDRAWFAILED");
        }

        uint256 toWithdraw = curveToken.balanceOf(address(this)).sub(crvBeforeBalance);

        //if we have less than 18 decimals we need to lower the amount out
        uint256 maxSlippage = toWithdraw.mul(DENOMINATOR.sub(slippageProtectionOut)).div(DENOMINATOR);
        if(want_decimals < 18){
            maxSlippage = maxSlippage.div(10 ** (uint256(uint8(18) - want_decimals)));
        }

        if(hasUnderlying){
            zapOut.remove_liquidity_one_coin(toWithdraw, curveId, maxSlippage, true);
        }else{
            zapOut.remove_liquidity_one_coin(toWithdraw, curveId, maxSlippage);
        }


        uint256 diff = want.balanceOf(address(this)).sub(wantBalanceBefore);

        if(diff > _amount){
            _liquidatedAmount = _amount;
        }else{
            _liquidatedAmount = diff;
            _loss = _amount.sub(diff);
        }

    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        yvToken.transfer(_newStrategy, yvToken.balanceOf(address(this)));
    }

    // Override this to add all tokens/tokenized positions this contract manages
    // on a *persistent* basis (e.g. not just for swapping back to want ephemerally)
    // NOTE: Do *not* include `want`, already included in `sweep` below
    //
    // Example:
    //
    //    function protectedTokens() internal override view returns (address[] memory) {
    //      address[] memory protected = new address[](3);
    //      protected[0] = tokenA;
    //      protected[1] = tokenB;
    //      protected[2] = tokenC;
    //      return protected;
    //    }
    function protectedTokens()
        internal
        override
        view
        returns (address[] memory)
    {

        address[] memory protected = new address[](1);
          protected[0] = address(yvToken);

          return protected;
    }
}
