// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "./interfaces/curve/Curve.sol";
import "./interfaces/curve/ICrvV3.sol";
import "./interfaces/erc20/IERC20Extended.sol";
import "./interfaces/IWETH.sol";

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

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    ICurveFi public basePool;
    ICurveFi public depositContract;
    ICrvV3 public curveToken;

    IWETH public constant weth = IWETH(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    address public constant uniswapRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address private constant threeCrv = 0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490;

    VaultAPI public yvToken;
    uint256 public lastInvest; // default is 0
    uint256 public minTimePerInvest;// = 3600;
    uint256 public maxSingleInvest;// // 2 hbtc per hour default
    uint256 public slippageProtectionIn;// = 50; //out of 10000. 50 = 0.5%
    uint256 public slippageProtectionOut;// = 50; //out of 10000. 50 = 0.5%
    uint256 public constant DENOMINATOR = 10_000;
    string internal strategyName;
    string public sscVersion;
    uint8 private want_decimals;
    bool public isOriginal = true;

    int128 public curveId;
    address public metaToken;
    bool public withdrawProtection;

    constructor(
        address _vault,
        uint256 _maxSingleInvest,
        uint256 _minTimePerInvest,
        uint256 _slippageProtectionIn,
        address _basePool,
        address _depositContract,
        address _yvToken,
        string memory _strategyName
    ) public BaseStrategy(_vault) {
         _initializeStrat(_maxSingleInvest, _minTimePerInvest, _slippageProtectionIn, _basePool, _depositContract, _yvToken, _strategyName);
    }

    function initialize(
        address _vault,
        address _strategist,
        uint256 _maxSingleInvest,
        uint256 _minTimePerInvest,
        uint256 _slippageProtectionIn,
        address _basePool,
        address _depositContract,
        address _yvToken,
        string memory _strategyName
    ) external {
        //note: initialise can only be called once. in _initialize in BaseStrategy we have: require(address(want) == address(0), "Strategy already initialized");
        _initialize(_vault, _strategist, _strategist, _strategist);
        _initializeStrat(_maxSingleInvest, _minTimePerInvest, _slippageProtectionIn, _basePool, _depositContract, _yvToken, _strategyName);
    }

    function _initializeStrat(
        uint256 _maxSingleInvest,
        uint256 _minTimePerInvest,
        uint256 _slippageProtectionIn,
        address _basePool,
        address _depositContract,
        address _yvToken,
        string memory _strategyName
    ) internal {
        require(want_decimals == 0, "Already Initialized");
        depositContract = ICurveFi(_depositContract);
        basePool = ICurveFi(_basePool);
        require(basePool.coins(1) == threeCrv);
        curveId = _findCurveId();
        if(curveId == 0){
            depositContract = basePool;
        }
        maxSingleInvest = _maxSingleInvest;
        minTimePerInvest = _minTimePerInvest;
        slippageProtectionIn = _slippageProtectionIn;
        slippageProtectionOut = _slippageProtectionIn; // use In to start with to save on stack
        strategyName = _strategyName;
        yvToken = VaultAPI(_yvToken);
        curveToken = ICrvV3(_basePool);
        _setupStatics();

    }
    function _findCurveId() internal view returns(int128){
        if(address(want) == address(0x6B175474E89094C44Da98b954EedeAC495271d0F)) return 1; // DAI
        if(address(want) == address(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)) return 2; // USDC
        if(address(want) == address(0xdAC17F958D2ee523a2206206994597C13D831ec7)) return 3; // USDT
        if(address(want) == basePool.coins(0)) return 0;
        revert();
    }
    function _setupStatics() internal {
        maxReportDelay = 86400;
        profitFactor = 1e30;
        minReportDelay = 3600;
        debtThreshold = 1e30;
        withdrawProtection = true;
        want_decimals = IERC20Extended(address(want)).decimals();
        sscVersion = "v5 factory 3pool";
        curveToken.approve(address(yvToken), type(uint256).max);
        if(curveId==0){
            want.safeApprove(address(basePool), type(uint256).max);
        }
        else{
            want.safeApprove(address(depositContract), type(uint256).max);
            curveToken.approve(address(depositContract), type(uint256).max);
        }
    }

    event Cloned(address indexed clone);

    function cloneSingleSidedCurve(
        address _vault,
        address _strategist,
        uint256 _maxSingleInvest,
        uint256 _minTimePerInvest,
        uint256 _slippageProtectionIn,
        address _basePool,
        address _depositContract,
        address _yvToken,
        string memory _strategyName
    ) external returns (address payable newStrategy) {
        require(isOriginal, "Clone inception!");
        bytes20 addressBytes = bytes20(address(this));

        assembly {
            // EIP-1167 bytecode
            let clone_code := mload(0x40)
            mstore(clone_code, 0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000000000000000000000)
            mstore(add(clone_code, 0x14), addressBytes)
            mstore(add(clone_code, 0x28), 0x5af43d82803e903d91602b57fd5bf30000000000000000000000000000000000)
            newStrategy := create(0, clone_code, 0x37)
        }

        Strategy(newStrategy).initialize(_vault, _strategist, _maxSingleInvest, _minTimePerInvest, _slippageProtectionIn, _basePool, _depositContract, _yvToken, _strategyName);

        emit Cloned(newStrategy);

    }

    function name() external override view returns (string memory) {
        return strategyName;
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

    function updateWithdrawProtection(bool _withdrawProtection) public onlyAuthorized {
        withdrawProtection = _withdrawProtection;
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

        return virtualPriceToWant().mul(tokens).div(1e18);
    }

    // we lose some precision here. but it shouldnt matter as we are underestimating
    function virtualPriceToWant() public view returns (uint256) {

        uint256 virtualPrice = basePool.get_virtual_price();

        if(want_decimals < 18){
            return virtualPrice.div(10 ** (uint256(uint8(18) - want_decimals)));
        }else{
            return virtualPrice;
        }

    }

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

        if(debt < currentValue) {
            //profit
            _profit = currentValue.sub(debt);
        }else{
            _loss = debt.sub(currentValue);
        }

        uint256 toFree = _debtPayment.add(_profit);

        if(toFree > wantBalance) {
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
    }

    function liquidateAllPositions() internal override returns (uint256 _amountFreed) {

        (_amountFreed, ) = liquidatePosition(1e36); //we can request a lot. dont use max because of overflow
    }

    function ethToWant(uint256 _amount) public override view returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = address(weth);
        path[1] = address(want);

        uint256[] memory amounts = IUni(uniswapRouter).getAmountsOut(_amount, path);

        return amounts[amounts.length - 1];
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {

        if (lastInvest.add(minTimePerInvest) > block.timestamp) {
            return;
        }

        // Invest the rest of the want
        uint256 _wantToInvest = Math.min(want.balanceOf(address(this)), maxSingleInvest);
        if (_wantToInvest == 0) {
            return;
        }

        uint256 expectedOut = _wantToInvest.mul(1e18).div(virtualPriceToWant());
        uint256 maxSlip = expectedOut.mul(DENOMINATOR.sub(slippageProtectionIn)).div(DENOMINATOR);

        
        if(curveId == 0){
            uint256[2] memory amounts;
            amounts[uint256(curveId)] = _wantToInvest;
            basePool.add_liquidity(amounts, maxSlip);
        }
        else{
            uint256[4] memory amounts;
            amounts[uint256(curveId)] = _wantToInvest;
            depositContract.add_liquidity(address(basePool), amounts, maxSlip);
        }
        
        // deposit to yearn vault
        yvToken.deposit();
        lastInvest = block.timestamp;
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss) {

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

        uint256 yBalance = yvToken.balanceOf(address(this));

        if(amountFromVault > yBalance) {

            amountFromVault = yBalance;
            //this is not loss. so we amend amount

            uint256 _amountOfCrv = amountFromVault.mul(pricePerFullShare).div(1e18);
            _amount = _amountOfCrv.mul(virtualPrice).div(1e18);
        }

        if (amountFromVault > 0) {
            yvToken.withdraw(amountFromVault);
            if (withdrawProtection) {
                //this tests that we liquidated all of the expected ytokens. Without it if we get back less then will mark it is loss
                require(yBalance.sub(yvToken.balanceOf(address(this))) >= amountFromVault.sub(1), "YVAULTWITHDRAWFAILED");
            }
        }

        uint256 toWithdraw = curveToken.balanceOf(address(this)).sub(crvBeforeBalance);

        if (toWithdraw > 0) {
            //if we have less than 18 decimals we need to lower the amount out
            uint256 maxSlippage = toWithdraw.mul(DENOMINATOR.sub(slippageProtectionOut)).div(DENOMINATOR);
            if(want_decimals < 18){
                maxSlippage = maxSlippage.div(10 ** (uint256(uint8(18) - want_decimals)));
            }
            if(curveId == 0){
                basePool.remove_liquidity_one_coin(toWithdraw, 0, maxSlippage);
            }
            else{
                depositContract.remove_liquidity_one_coin(address(basePool), toWithdraw, curveId, maxSlippage);
            }
        }

        uint256 diff = want.balanceOf(address(this)).sub(wantBalanceBefore);

        if(diff > _amount){
            _liquidatedAmount = _amount;
        }else{
            _liquidatedAmount = diff;
            _loss = _amount.sub(diff);
        }

    }

    function prepareMigration(address _newStrategy) internal override {
        yvToken.transfer(_newStrategy, yvToken.balanceOf(address(this)));
    }

    function protectedTokens()
        internal
        override
        view
        returns (address[] memory) {

        address[] memory protected = new address[](1);
          protected[0] = address(yvToken);

          return protected;
    }

    receive() external payable {}
}