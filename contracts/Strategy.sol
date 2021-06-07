// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "./Interfaces/curve/Curve.sol";
import "./Interfaces/curve/ICrvV3.sol";
import "./Interfaces/erc20/IERC20Extended.sol";
import "./Interfaces/Yearn/IVaultV2.sol";

import "./Synthetix.sol";

// These are the core Yearn libraries
import "@yearnvaults/contracts/BaseStrategy.sol";

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";

interface IUni {
    function getAmountsOut(uint256 amountIn, address[] calldata path)
        external
        view
        returns (uint256[] memory amounts);
}

contract Strategy is BaseStrategy, Synthetix {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    ICurveFi public curvePool;
    ICrvV3 public curveToken;

    uint256 public susdBuffer; // 10% (over 10_000 BPS) amount of sUSD that should not be exchanged for sETH

    address public constant weth = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public constant uniswapRouter =
        0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;

    IVaultV2 public yvToken;

    uint256 public lastInvest;
    uint256 public minTimePerInvest; // = 3600;
    uint256 public maxSingleInvest; // // 2 hbtc per hour default
    uint256 public slippageProtectionIn; // = 50; //out of 10000. 50 = 0.5%
    uint256 public slippageProtectionOut; // = 50; //out of 10000. 50 = 0.5%
    uint256 public constant DENOMINATOR = 10_000;
    uint256 public maxLoss; // maximum loss allowed from yVault withdrawal default value: 1 (in BPS)
    uint8 private synth_decimals;

    uint256 internal constant DUST_THRESHOLD = 10_000;

    int128 public curveId;
    uint256 public poolSize;
    bool public hasUnderlying;

    bool public withdrawProtection;

    constructor(
        address _vault,
        address _curvePool,
        address _curveToken,
        address _yvToken,
        uint256 _poolSize,
        bool _hasUnderlying,
        bytes32 _synth
    ) public BaseStrategy(_vault) {
        _initializeSynthetix(_synth);
        _initializeStrat(
            _curvePool,
            _curveToken,
            _yvToken,
            _poolSize,
            _hasUnderlying
        );
    }

    function initialize(
        address _vault,
        address _curvePool,
        address _curveToken,
        address _yvToken,
        uint256 _poolSize,
        bool _hasUnderlying,
        bytes32 _synth
    ) external {
        //note: initialise can only be called once. in _initialize in BaseStrategy we have: require(address(want) == address(0), "Strategy already initialized");
        _initialize(_vault, msg.sender, msg.sender, msg.sender);
        _initializeSynthetix(_synth);
        _initializeStrat(
            _curvePool,
            _curveToken,
            _yvToken,
            _poolSize,
            _hasUnderlying
        );
    }

    function _initializeStrat(
        address _curvePool,
        address _curveToken,
        address _yvToken,
        uint256 _poolSize,
        bool _hasUnderlying
    ) internal {
        require(
            address(curvePool) == address(curvePool),
            "Already Initialized"
        );
        require(_poolSize > 1 && _poolSize < 5, "incorrect pool size");
        require(address(want) == address(_synthsUSD()), "want must be sUSD");

        curvePool = ICurveFi(_curvePool);

        if (
            curvePool.coins(0) == address(_synthCoin()) ||
            (_hasUnderlying &&
                curvePool.underlying_coins(0) == address(_synthCoin()))
        ) {
            curveId = 0;
        } else if (
            curvePool.coins(1) == address(_synthCoin()) ||
            (_hasUnderlying &&
                curvePool.underlying_coins(1) == address(_synthCoin()))
        ) {
            curveId = 1;
        } else if (
            curvePool.coins(2) == address(_synthCoin()) ||
            (_hasUnderlying &&
                curvePool.underlying_coins(2) == address(_synthCoin()))
        ) {
            curveId = 2;
        } else if (
            curvePool.coins(3) == address(_synthCoin()) ||
            (_hasUnderlying &&
                curvePool.underlying_coins(3) == address(_synthCoin()))
        ) {
            //will revert if there are not enough coins
            curveId = 3;
        } else {
            require(false, "incorrect want for curve pool");
        }

        maxSingleInvest = type(uint256).max; // save on stack
        // minTimePerInvest = _minTimePerInvest; // save on stack
        slippageProtectionIn = 50; // default to save on stack
        slippageProtectionOut = 50; // default to save on stack

        poolSize = _poolSize;
        hasUnderlying = _hasUnderlying;

        yvToken = IVaultV2(_yvToken);
        curveToken = ICrvV3(_curveToken);

        _setupStatics();
    }

    function _setupStatics() internal {
        maxReportDelay = 86400;
        profitFactor = 1500;
        minReportDelay = 3600;
        debtThreshold = 100 * 1e18;
        withdrawProtection = true;
        maxLoss = 1;
        susdBuffer = 1_000; // 10% over 10_000 BIPS
        synth_decimals = IERC20Extended(address(_synthCoin())).decimals();
        want.safeApprove(address(curvePool), type(uint256).max);
        curveToken.approve(address(yvToken), type(uint256).max);
    }

    event Cloned(address indexed clone);

    function cloneSingleSidedCurve(
        address _vault,
        address _curvePool,
        address _curveToken,
        address _yvToken,
        uint256 _poolSize,
        bool _hasUnderlying,
        bytes32 _synth
    ) external returns (address newStrategy) {
        bytes20 addressBytes = bytes20(address(this));

        assembly {
            // EIP-1167 bytecode
            let clone_code := mload(0x40)
            mstore(
                clone_code,
                0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000000000000000000000
            )
            mstore(add(clone_code, 0x14), addressBytes)
            mstore(
                add(clone_code, 0x28),
                0x5af43d82803e903d91602b57fd5bf30000000000000000000000000000000000
            )
            newStrategy := create(0, clone_code, 0x37)
        }
        Strategy(newStrategy).initialize(
            _vault,
            _curvePool,
            _curveToken,
            _yvToken,
            _poolSize,
            _hasUnderlying,
            _synth
        );

        emit Cloned(newStrategy);
    }

    function name() external view override returns (string memory) {
        return
            string(
                abi.encodePacked(
                    "SingleSidedCrvSynth",
                    IERC20Extended(address(_synthCoin())).symbol()
                )
            );
    }

    function updateMinTimePerInvest(uint256 _minTimePerInvest)
        public
        onlyAuthorized
    {
        minTimePerInvest = _minTimePerInvest;
    }

    function updateSUSDBuffer(uint256 _susdBuffer) public onlyAuthorized {
        // IN BIPS
        require(_susdBuffer <= 10_000, "!too high");
        susdBuffer = _susdBuffer;
    }

    function updatemaxSingleInvest(uint256 _maxSingleInvest)
        public
        onlyAuthorized
    {
        maxSingleInvest = _maxSingleInvest;
    }

    function updateSlippageProtectionIn(uint256 _slippageProtectionIn)
        public
        onlyAuthorized
    {
        slippageProtectionIn = _slippageProtectionIn;
    }

    function updateSlippageProtectionOut(uint256 _slippageProtectionOut)
        public
        onlyAuthorized
    {
        slippageProtectionOut = _slippageProtectionOut;
    }

    function updateWithdrawProtection(bool _withdrawProtection)
        external
        onlyAuthorized
    {
        withdrawProtection = _withdrawProtection;
    }

    function updateMaxLoss(uint256 _maxLoss) public onlyAuthorized {
        require(_maxLoss <= 10_000);
        maxLoss = _maxLoss;
    }

    function delegatedAssets() public view override returns (uint256) {
        return
            Math.min(
                curveTokenToWant(curveTokensInYVault()),
                vault.strategies(address(this)).totalDebt
            );
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        uint256 totalCurveTokens = curveTokensInYVault().add(
            curveToken.balanceOf(address(this))
        );
        // NOTE: want is always sUSD so we directly use _balanceOfSUSD
        // NOTE: _synthToSUSD takes into account future fees in which the strategy will incur for exchanging synth for sUSD
        return
            _balanceOfSUSD().add(_synthToSUSD(_balanceOfSynth())).add(
                curveTokenToWant(totalCurveTokens)
            );
    }

    // returns value of total
    function curveTokenToWant(uint256 tokens) public view returns (uint256) {
        if (tokens == 0) {
            return 0;
        }

        //we want to choose lower value of virtual price and amount we really get out
        //this means we will always underestimate current assets.
        uint256 virtualOut = virtualPriceToSynth().mul(tokens).div(1e18);

        return _synthToSUSD(virtualOut);
    }

    //we lose some precision here. but it shouldnt matter as we are underestimating
    function virtualPriceToSynth() public view returns (uint256) {
        return curvePool.get_virtual_price();
    }

    function curveTokensInYVault() public view returns (uint256) {
        uint256 balance = yvToken.balanceOf(address(this));

        if (yvToken.totalSupply() == 0) {
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
        uint256 wantBalance = _balanceOfSUSD(); // want is always sUSD

        // we check against estimatedTotalAssets
        if (debt < currentValue) {
            //profit
            _profit = currentValue.sub(debt);
            // NOTE: the strategy will only be able to serve profit payment up to buffer amount
            // we limit profit and try to delay its reporting until there is enough unlocked want to repay it to the vault
            _profit = Math.min(wantBalance, _profit);
        } else {
            _loss = debt.sub(currentValue);
        }

        uint256 toFree = _debtPayment.add(_profit);
        // if the strategy needs to exchange sETH into sUSD, the waiting period will kick in and the vault.report will revert !!!
        // this only works if the strategy has been previously unwinded using BUFFER = 100% OR manual function
        // otherwise, max amount "toFree" is wantBalance (which should be the buffer, which should be setted to be able to serve profit taking)
        if (toFree > wantBalance) {
            toFree = toFree.sub(wantBalance);

            (, uint256 withdrawalLoss) = withdrawSomeWant(toFree);

            //when we withdraw we can lose money in the withdrawal
            if (withdrawalLoss < _profit) {
                _profit = _profit.sub(withdrawalLoss);
            } else {
                _loss = _loss.add(withdrawalLoss.sub(_profit));
                _profit = 0;
            }

            wantBalance = _balanceOfSUSD();

            if (wantBalance < _profit) {
                _profit = wantBalance;
                _debtPayment = 0;
            } else if (wantBalance < _debtPayment.add(_profit)) {
                _debtPayment = wantBalance.sub(_profit);
            }
        }
    }

    function harvestTrigger(uint256 callCost)
        public
        view
        override
        returns (bool)
    {
        uint256 wantCallCost;

        if (address(want) == weth) {
            wantCallCost = callCost;
        } else {
            wantCallCost = _ethToWant(callCost);
        }

        return super.harvestTrigger(wantCallCost);
    }

    function _ethToWant(uint256 _amount) internal view returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = weth;
        path[1] = address(want);

        uint256[] memory amounts = IUni(uniswapRouter).getAmountsOut(
            _amount,
            path
        );

        return amounts[amounts.length - 1];
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        if (lastInvest.add(minTimePerInvest) > block.timestamp) {
            return;
        }

        // 1. Check if we can invest Synth
        uint256 looseSynth = _balanceOfSynth();
        uint256 _sUSDBalance = _balanceOfSUSD();

        // we calculate how much we need to keep in buffer
        // all the amount over it will be converted into Synth
        uint256 totalDebt = vault.strategies(address(this)).totalDebt; // in sUSD (want)
        uint256 buffer = totalDebt.mul(susdBuffer).div(DENOMINATOR);

        uint256 _sUSDToInvest = _sUSDBalance > buffer
            ? _sUSDBalance.sub(buffer)
            : 0;
        uint256 _sUSDNeeded = _sUSDToInvest == 0 ? buffer.sub(_sUSDBalance) : 0;
        uint256 _synthToSell = _sUSDNeeded > 0
            ? _synthFromSUSD(_sUSDNeeded)
            : 0; // amount of Synth that we need to sell to refill buffer
        uint256 _synthToInvest = looseSynth > _synthToSell
            ? looseSynth.sub(_synthToSell)
            : 0;
        // how much loose Synth, available to invest, we will have after buying sUSD?
        // if we cannot invest synth (either due to Synthetix waiting period OR because we don't have enough available)
        // we buy synth with sUSD and return (due to Synthetix waiting period we cannot do anything else)
        if (
            _exchanger().maxSecsLeftInWaitingPeriod(
                address(this),
                synthCurrencyKey
            ) ==
            0 &&
            _synthToInvest > DUST_THRESHOLD
        ) {
            // 2. Supply liquidity (single sided) to Curve Pool
            // calculate LP tokens that we will receive
            uint256 expectedOut = _synthToInvest.mul(1e18).div(
                virtualPriceToSynth()
            );

            // Minimum amount of LP tokens to mint
            uint256 minMint = expectedOut
            .mul(DENOMINATOR.sub(slippageProtectionIn))
            .div(DENOMINATOR);

            ensureAllowance(
                address(curvePool),
                address(_synthCoin()),
                _synthToInvest
            );

            // NOTE: pool size cannot be more than 4 or less than 2
            if (poolSize == 2) {
                uint256[2] memory amounts;
                amounts[uint256(curveId)] = _synthToInvest;
                if (hasUnderlying) {
                    curvePool.add_liquidity(amounts, minMint, true);
                } else {
                    curvePool.add_liquidity(amounts, minMint);
                }
            } else if (poolSize == 3) {
                uint256[3] memory amounts;
                amounts[uint256(curveId)] = _synthToInvest;
                if (hasUnderlying) {
                    curvePool.add_liquidity(amounts, minMint, true);
                } else {
                    curvePool.add_liquidity(amounts, minMint);
                }
            } else {
                uint256[4] memory amounts;
                amounts[uint256(curveId)] = _synthToInvest;
                if (hasUnderlying) {
                    curvePool.add_liquidity(amounts, minMint, true);
                } else {
                    curvePool.add_liquidity(amounts, minMint);
                }
            }

            // 3. Deposit LP tokens in yVault
            uint256 lpBalance = curveToken.balanceOf(address(this));

            if (lpBalance > 0) {
                ensureAllowance(
                    address(yvToken),
                    address(curveToken),
                    lpBalance
                );
                yvToken.deposit();
            }
            lastInvest = block.timestamp;
        }

        if (_synthToSell == 0) {
            // This will invest all available sUSD (exchanging to Synth first)
            // Exchange amount of sUSD to Synth
            _sUSDToInvest = Math.min(
                _sUSDToInvest,
                _sUSDFromSynth(maxSingleInvest)
            );
            if (_sUSDToInvest == 0) {
                return;
            }
            exchangeSUSDToSynth(_sUSDToInvest);
            // now the waiting period starts
        } else if (_synthToSell >= DUST_THRESHOLD) {
            // this means that we need to refill the buffer
            // we may have already some uninvested Synth so we use it (and avoid withdrawing from Curve's Pool)
            uint256 available = _synthToSUSD(_balanceOfSynth());
            uint256 sUSDToWithdraw = _sUSDNeeded > available
                ? _sUSDNeeded.sub(available)
                : 0;
            // this will withdraw and sell full balance of Synth (inside withdrawSomeWant)
            if (sUSDToWithdraw > 0) {
                withdrawSomeWant(sUSDToWithdraw);
            }
            // now the waiting period starts
        }
    }

    function ensureAllowance(
        address _spender,
        address _token,
        uint256 _amount
    ) internal {
        if (IERC20(_token).allowance(address(this), _spender) < _amount) {
            IERC20(_token).safeApprove(_spender, 0);
            IERC20(_token).safeApprove(_spender, type(uint256).max);
        }
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        uint256 wantBal = _balanceOfSUSD(); // want is always sUSD
        if (wantBal < _amountNeeded) {
            (_liquidatedAmount, _loss) = withdrawSomeWant(
                _amountNeeded.sub(wantBal)
            );
        }

        _liquidatedAmount = Math.min(
            _amountNeeded,
            _liquidatedAmount.add(wantBal)
        );
    }

    //safe to enter more than we have
    function withdrawSomeWant(uint256 _amount)
        internal
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        uint256 sUSDBalanceBefore = _balanceOfSUSD();

        // LPtoken virtual price in Synth
        uint256 virtualPrice = virtualPriceToSynth();

        // 1. We calculate how many LP tokens we need to burn to get requested want
        uint256 amountWeNeedFromVirtualPrice = _synthFromSUSD(_amount)
        .mul(1e18)
        .div(virtualPrice);

        // 2. Withdraw LP tokens from yVault
        uint256 crvBeforeBalance = curveToken.balanceOf(address(this));

        // Calculate how many shares we need to burn to get the amount of LP tokens that we want
        uint256 pricePerFullShare = yvToken.pricePerShare();
        uint256 amountFromVault = amountWeNeedFromVirtualPrice.mul(1e18).div(
            pricePerFullShare
        );

        // cap to our yShares balance
        uint256 yBalance = yvToken.balanceOf(address(this));
        if (amountFromVault > yBalance) {
            amountFromVault = yBalance;
            // this is not loss. so we amend amount

            uint256 _amountOfCrv = amountFromVault.mul(pricePerFullShare).div(
                1e18
            );
            _amount = _amountOfCrv.mul(virtualPrice).div(1e18);
        }

        if (amountFromVault > 0) {
            // Added explicit maxLoss protection in case something goes wrong
            yvToken.withdraw(amountFromVault, address(this), maxLoss);

            if (withdrawProtection) {
                //this tests that we liquidated all of the expected ytokens. Without it if we get back less then will mark it is loss
                require(
                    yBalance.sub(yvToken.balanceOf(address(this))) >=
                        amountFromVault.sub(1),
                    "YVAULTWITHDRAWFAILED"
                );
            }

            // 3. Get coins back by burning LP tokens
            // We are going to burn the amount of LP tokens we just withdrew
            uint256 toBurn = curveToken.balanceOf(address(this)).sub(
                crvBeforeBalance
            );

            // amount of synth we expect to receive
            uint256 toWithdraw = toBurn.mul(virtualPriceToSynth()).div(1e18);

            // minimum amount of coins we are going to receive
            uint256 minAmount = toWithdraw
            .mul(DENOMINATOR.sub(slippageProtectionOut))
            .div(DENOMINATOR);

            if (hasUnderlying) {
                curvePool.remove_liquidity_one_coin(
                    toBurn,
                    curveId,
                    minAmount,
                    true
                );
            } else {
                curvePool.remove_liquidity_one_coin(toBurn, curveId, minAmount);
            }
        }

        // 4. Exchange the full balance of Synth for sUSD (want)
        if (_balanceOfSynth() > DUST_THRESHOLD) {
            exchangeSynthToSUSD();
        }

        uint256 diff = _balanceOfSUSD().sub(sUSDBalanceBefore);
        if (diff > _amount) {
            _liquidatedAmount = _amount;
        } else {
            _liquidatedAmount = diff;
            _loss = _amount.sub(diff);
        }
    }

    function manualRemoveFullLiquidity()
        external
        onlyGovernance
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        // It will remove max amount of assets and trade sETH for sUSD
        // the Synthetix waiting period will start (and harvest can be called 6 mins later)
        (_liquidatedAmount, _loss) = withdrawSomeWant(estimatedTotalAssets());
    }

    function prepareMigration(address _newStrategy) internal override {
        // only yvToken and want balances should be required but we do all of them to avoid having them stuck in strategy's middle steps
        // want balance is sent from BaseStrategy's migrate method
        yvToken.transfer(_newStrategy, yvToken.balanceOf(address(this)));
        curveToken.transfer(_newStrategy, curveToken.balanceOf(address(this)));
        IERC20(address(_synthCoin())).transfer(_newStrategy, _balanceOfSynth());
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
        view
        override
        returns (address[] memory)
    {
        address[] memory protected = new address[](1);
        protected[0] = address(yvToken);

        return protected;
    }
}
