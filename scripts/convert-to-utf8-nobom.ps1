Param(
  [Parameter(Mandatory=$true)][string]$Path
)
$t = Get-Content -Raw -Encoding Auto $Path
$t = $t -replace "`r?`n","`r`n"
$enc = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($Path, $t, $enc)
