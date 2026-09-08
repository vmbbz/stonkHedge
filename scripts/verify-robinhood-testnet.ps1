[CmdletBinding()]
param(
    [string]$ManifestPath = (Join-Path (Split-Path $PSScriptRoot -Parent) "manifests\chains\robinhood-testnet-46630.json"),
    [string]$RpcUrl,
    [switch]$SkipFundingGate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Cast {
    param([Parameter(Mandatory)] [string[]]$Arguments)

    $output = & cast @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "cast $($Arguments -join ' ') failed`n$($output -join "`n")"
    }
    return ($output -join "`n").Trim()
}

function Get-Scalar {
    param([Parameter(Mandatory)] [string]$Value)
    return ($Value -split "\s+")[0]
}

function Write-Check {
    param(
        [Parameter(Mandatory)] [ValidateSet("PASS", "FAIL", "BLOCKED", "SKIPPED")] [string]$Status,
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [string]$Detail
    )

    Write-Host ("[{0}] {1}: {2}" -f $Status, $Name, $Detail)
    if ($Status -in @("FAIL", "BLOCKED")) {
        $script:VerificationFailed = $true
    }
}

function Test-Equal {
    param(
        [Parameter(Mandatory)] [string]$Name,
        [AllowEmptyString()] [string]$Actual,
        [AllowEmptyString()] [string]$Expected
    )

    $status = if ($Actual -ieq $Expected) { "PASS" } else { "FAIL" }
    Write-Check -Status $status -Name $Name -Detail "$Actual (expected $Expected)"
}

function Test-CodeIdentity {
    param(
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [string]$Address,
        [Parameter(Mandatory)] [int]$ExpectedBytes,
        [Parameter(Mandatory)] [string]$ExpectedHash,
        [Parameter(Mandatory)] [string]$Rpc
    )

    $code = Invoke-Cast -Arguments @("code", $Address, "--rpc-url", $Rpc)
    $runtimeBytes = if ($code -eq "0x") { 0 } else { [int](($code.Length - 2) / 2) }
    $codeHash = Invoke-Cast -Arguments @("codehash", $Address, "--rpc-url", $Rpc)
    $status = if (($runtimeBytes -eq $ExpectedBytes) -and ($codeHash -ieq $ExpectedHash)) { "PASS" } else { "FAIL" }
    Write-Check -Status $status -Name "$Name code" -Detail "$Address bytes=$runtimeBytes hash=$codeHash"
}

if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Chain manifest not found: $ManifestPath"
}
if (-not (Get-Command cast -ErrorAction SilentlyContinue)) {
    throw "Foundry cast is required but was not found on PATH."
}

$manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$rpc = if ($RpcUrl) { $RpcUrl } else { $manifest.network.rpcUrl }
$script:VerificationFailed = $false

$chainId = Invoke-Cast -Arguments @("chain-id", "--rpc-url", $rpc)
Test-Equal -Name "chain ID" -Actual $chainId -Expected ([string]$manifest.network.chainId)
if ($chainId -ne [string]$manifest.network.chainId) {
    Write-Host "Wrong network; no contract calls were attempted."
    exit 1
}

$head = Invoke-Cast -Arguments @("block-number", "--rpc-url", $rpc)
Write-Check -Status "PASS" -Name "RPC head" -Detail $head

foreach ($property in $manifest.infrastructure.PSObject.Properties) {
    $contract = $property.Value
    Test-CodeIdentity -Name $property.Name -Address $contract.address -ExpectedBytes $contract.runtimeBytes -ExpectedHash $contract.runtimeCodeHash -Rpc $rpc
}

$pool = $manifest.infrastructure.poolManager
$poolOwner = Invoke-Cast -Arguments @("call", $pool.address, "owner()(address)", "--rpc-url", $rpc)
Test-Equal -Name "PoolManager owner" -Actual $poolOwner -Expected $pool.owner
$poolOwnerCode = Invoke-Cast -Arguments @("code", $pool.owner, "--rpc-url", $rpc)
$poolOwnerBytes = if ($poolOwnerCode -eq "0x") { 0 } else { [int](($poolOwnerCode.Length - 2) / 2) }
Test-Equal -Name "PoolManager owner runtime bytes" -Actual ([string]$poolOwnerBytes) -Expected ([string]$pool.ownerRuntimeBytes)
$feeController = Invoke-Cast -Arguments @("call", $pool.address, "protocolFeeController()(address)", "--rpc-url", $rpc)
Test-Equal -Name "PoolManager protocol fee controller" -Actual $feeController -Expected $pool.protocolFeeController

$positionManager = $manifest.infrastructure.positionManager
$wiredPoolManager = Invoke-Cast -Arguments @("call", $positionManager.address, "poolManager()(address)", "--rpc-url", $rpc)
Test-Equal -Name "PositionManager PoolManager wiring" -Actual $wiredPoolManager -Expected $positionManager.poolManager

$registry = $manifest.sharedStockInfrastructure
Test-CodeIdentity -Name "Stock registry/beacon" -Address $registry.registryAndBeacon -ExpectedBytes $registry.registryRuntimeBytes -ExpectedHash $registry.registryRuntimeCodeHash -Rpc $rpc
$registryPaused = Invoke-Cast -Arguments @("call", $registry.registryAndBeacon, "paused()(bool)", "--rpc-url", $rpc)
Test-Equal -Name "Stock registry global pause" -Actual $registryPaused -Expected ([string]$registry.registryPaused).ToLowerInvariant()
$stockImplementation = Invoke-Cast -Arguments @("call", $registry.registryAndBeacon, "implementation()(address)", "--rpc-url", $rpc)
Test-Equal -Name "Stock beacon implementation" -Actual $stockImplementation -Expected $registry.implementation
Test-CodeIdentity -Name "Stock implementation" -Address $registry.implementation -ExpectedBytes $registry.implementationRuntimeBytes -ExpectedHash $registry.implementationRuntimeCodeHash -Rpc $rpc

$deployer = $manifest.deployer
$deployerBlocked = Invoke-Cast -Arguments @("call", $registry.registryAndBeacon, "isBlocked(address)(bool)", $deployer.address, "--rpc-url", $rpc)
Test-Equal -Name "deployer Stock registry block status" -Actual $deployerBlocked -Expected ([string]$deployer.blockedByStockRegistry).ToLowerInvariant()

$positiveStockBalance = $false
foreach ($stock in $manifest.stockTokens) {
    Test-CodeIdentity -Name "$($stock.symbol) proxy" -Address $stock.address -ExpectedBytes $registry.proxyRuntimeBytes -ExpectedHash $registry.proxyRuntimeCodeHash -Rpc $rpc

    $actualRegistry = Invoke-Cast -Arguments @("call", $stock.address, "ACCESS_CONTROLLED_REGISTRY()(address)", "--rpc-url", $rpc)
    Test-Equal -Name "$($stock.symbol) registry" -Actual $actualRegistry -Expected $registry.registryAndBeacon
    $symbol = (Invoke-Cast -Arguments @("call", $stock.address, "symbol()(string)", "--rpc-url", $rpc)).Trim('"')
    Test-Equal -Name "$($stock.symbol) symbol" -Actual $symbol -Expected $stock.symbol
    $name = (Invoke-Cast -Arguments @("call", $stock.address, "name()(string)", "--rpc-url", $rpc)).Trim('"')
    Test-Equal -Name "$($stock.symbol) name" -Actual $name -Expected $stock.name
    $decimals = Get-Scalar (Invoke-Cast -Arguments @("call", $stock.address, "decimals()(uint8)", "--rpc-url", $rpc))
    Test-Equal -Name "$($stock.symbol) decimals" -Actual $decimals -Expected ([string]$manifest.requiredStockState.decimals)
    $paused = Invoke-Cast -Arguments @("call", $stock.address, "paused()(bool)", "--rpc-url", $rpc)
    Test-Equal -Name "$($stock.symbol) global pause" -Actual $paused -Expected ([string]$manifest.requiredStockState.paused).ToLowerInvariant()
    $tokenPaused = Invoke-Cast -Arguments @("call", $stock.address, "tokenPaused()(bool)", "--rpc-url", $rpc)
    Test-Equal -Name "$($stock.symbol) token pause" -Actual $tokenPaused -Expected ([string]$manifest.requiredStockState.tokenPaused).ToLowerInvariant()
    $uiMultiplier = Get-Scalar (Invoke-Cast -Arguments @("call", $stock.address, "uiMultiplier()(uint256)", "--rpc-url", $rpc))
    Test-Equal -Name "$($stock.symbol) UI multiplier" -Actual $uiMultiplier -Expected $manifest.requiredStockState.uiMultiplier
    $newUiMultiplier = Get-Scalar (Invoke-Cast -Arguments @("call", $stock.address, "newUIMultiplier()(uint256)", "--rpc-url", $rpc))
    Test-Equal -Name "$($stock.symbol) pending UI multiplier" -Actual $newUiMultiplier -Expected $manifest.requiredStockState.newUiMultiplier
    $effectiveAt = Get-Scalar (Invoke-Cast -Arguments @("call", $stock.address, "effectiveAt()(uint256)", "--rpc-url", $rpc))
    Test-Equal -Name "$($stock.symbol) multiplier effective time" -Actual $effectiveAt -Expected $manifest.requiredStockState.effectiveAt

    $balance = Get-Scalar (Invoke-Cast -Arguments @("call", $stock.address, "balanceOf(address)(uint256)", $deployer.address, "--rpc-url", $rpc))
    if ([System.Numerics.BigInteger]::Parse($balance) -gt [System.Numerics.BigInteger]::Zero) {
        $positiveStockBalance = $true
    }
    Write-Check -Status "PASS" -Name "$($stock.symbol) deployer balance read" -Detail "$balance wei-units"
}

foreach ($property in $manifest.quoteAssets.PSObject.Properties) {
    $token = $property.Value
    Test-CodeIdentity -Name $property.Name -Address $token.address -ExpectedBytes $token.runtimeBytes -ExpectedHash $token.runtimeCodeHash -Rpc $rpc
    $symbol = (Invoke-Cast -Arguments @("call", $token.address, "symbol()(string)", "--rpc-url", $rpc)).Trim('"')
    Test-Equal -Name "$($property.Name) symbol" -Actual $symbol -Expected $token.symbol
    $decimals = Get-Scalar (Invoke-Cast -Arguments @("call", $token.address, "decimals()(uint8)", "--rpc-url", $rpc))
    Test-Equal -Name "$($property.Name) decimals" -Actual $decimals -Expected ([string]$token.decimals)
}

$nativeBalance = Get-Scalar (Invoke-Cast -Arguments @("balance", $deployer.address, "--rpc-url", $rpc))
$nonce = Get-Scalar (Invoke-Cast -Arguments @("nonce", $deployer.address, "--rpc-url", $rpc))
Write-Check -Status "PASS" -Name "deployer nonce read" -Detail $nonce

if ($SkipFundingGate) {
    Write-Check -Status "SKIPPED" -Name "deployer funding" -Detail "native=$nativeBalance; positive Stock Token balance=$positiveStockBalance"
}
else {
    $nativeReady = [System.Numerics.BigInteger]::Parse($nativeBalance) -ge [System.Numerics.BigInteger]::Parse($deployer.minimumNativeWeiForPreflight)
    $stockReady = (-not $deployer.requireAtLeastOnePositiveStockBalance) -or $positiveStockBalance
    $fundingStatus = if ($nativeReady -and $stockReady) { "PASS" } else { "BLOCKED" }
    Write-Check -Status $fundingStatus -Name "deployer funding" -Detail "native=$nativeBalance; positive Stock Token balance=$positiveStockBalance"
}

if ($script:VerificationFailed) {
    Write-Host "Robinhood testnet verification did not pass. Do not simulate or broadcast from this manifest."
    exit 1
}

Write-Host "Robinhood testnet verification passed. This validates identity and current health, not independent review or deployment authorization."
exit 0
