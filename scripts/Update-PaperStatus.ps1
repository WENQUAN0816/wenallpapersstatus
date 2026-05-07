Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ReadmePath = Join-Path $RepoRoot "README.md"
$ChartHtmlPath = Join-Path $RepoRoot "status_chart.html"
$SvgPath = Join-Path $RepoRoot "status_bar_chart.svg"
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$NewLine = "`n"

$Statuses = @(
    [pscustomobject]@{ Name = "待投稿"; Icon = "&#9898;"; Fill = "#f2f2f2"; Stroke = "#9ca3af" },
    [pscustomobject]@{ Name = "需修订"; Icon = "&#128150;"; Fill = "#ffd9ec"; Stroke = "#ec4899" },
    [pscustomobject]@{ Name = "内审中"; Icon = "&#128993;"; Fill = "#fff8d9"; Stroke = "#eab308" },
    [pscustomobject]@{ Name = "外审中"; Icon = "&#128994;"; Fill = "#e8f9ee"; Stroke = "#22c55e" }
)

$StatusByName = @{}
$StatusByIcon = @{}
$StatusByFill = @{}
for ($i = 0; $i -lt $Statuses.Count; $i++) {
    $StatusByName[$Statuses[$i].Name] = [pscustomobject]@{
        Order = $i
        Meta = $Statuses[$i]
    }
    $StatusByIcon[$Statuses[$i].Icon] = $Statuses[$i].Name
    $StatusByFill[$Statuses[$i].Fill] = $Statuses[$i].Name
}

$LegacyStatus = @{
    "待初审" = "内审中"
    "初审中" = "内审中"
}

function Get-NormalizedStatus {
    param([string]$Status)

    $Status = $Status.Trim()
    if ($LegacyStatus.ContainsKey($Status)) {
        return $LegacyStatus[$Status]
    }
    return $Status
}

function Normalize-StatusRow {
    param(
        [string]$Row,
        [string]$Status
    )

    $Meta = $StatusByName[$Status].Meta
    $Row = [regex]::Replace(
        $Row,
        'bgcolor="#[0-9A-Fa-f]{6}" style="background-color:#[0-9A-Fa-f]{6}',
        "bgcolor=""$($Meta.Fill)"" style=""background-color:$($Meta.Fill)"
    )
    $Row = [regex]::Replace(
        $Row,
        '(<td bgcolor="#[0-9A-Fa-f]{6}" style="background-color:#[0-9A-Fa-f]{6}; vertical-align: top; white-space: nowrap;">)&#[0-9]+;(?:\s*[^<]+)?(</td>)',
        "`${1}$($Meta.Icon)`${2}",
        1
    )
    $Row = Clear-TrackCellChinese $Row
    return $Row
}

function Get-StatusFromRow {
    param([string]$Row)

    $StatusCellMatch = [regex]::Match($Row, '<td bgcolor="(?<fill>#[0-9A-Fa-f]{6})" style="background-color:#[0-9A-Fa-f]{6}; vertical-align: top; white-space: nowrap;">(?<icon>&#[0-9]+;)(?:\s*(?<status>[^<]+))?</td>')
    if (-not $StatusCellMatch.Success) {
        return $null
    }

    $StatusText = $StatusCellMatch.Groups["status"].Value.Trim()
    if ($StatusText) {
        return Get-NormalizedStatus $StatusText
    }

    $Icon = $StatusCellMatch.Groups["icon"].Value
    if ($StatusByIcon.ContainsKey($Icon)) {
        return $StatusByIcon[$Icon]
    }

    $Fill = $StatusCellMatch.Groups["fill"].Value.ToLowerInvariant()
    if ($StatusByFill.ContainsKey($Fill)) {
        return $StatusByFill[$Fill]
    }

    return $null
}

function Remove-ChineseText {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return ""
    }

    $Text = [System.Net.WebUtility]::HtmlDecode($Text)
    $Text = $Text.Replace("（", "(").Replace("）", ")").Replace("；", ";").Replace("，", ",").Replace("：", ":").Replace("。", ".")
    $Text = [regex]::Replace($Text, '[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]+', '')
    $Text = [regex]::Replace($Text, '\(\s*[;,:\s.-]*\)', '')
    $Text = [regex]::Replace($Text, '\(\s*[;,:\s]*(?<inner>[^)]*?)\s*\)', {
        param($Match)
        $Inner = [regex]::Replace($Match.Groups["inner"].Value, '^[;,:\s]+|[;,:\s]+$', '')
        if ([string]::IsNullOrWhiteSpace($Inner)) {
            return ""
        }
        return "($Inner)"
    })
    $Text = [regex]::Replace($Text, '\s+([,;:)])', '$1')
    $Text = [regex]::Replace($Text, '([(])\s+', '$1')
    $Text = [regex]::Replace($Text, '\s{2,}', ' ').Trim()
    return [System.Net.WebUtility]::HtmlEncode($Text)
}

function Clear-TrackCellChinese {
    param([string]$Row)

    $CellMatches = [regex]::Matches($Row, '(?s)<td(?<attrs>[^>]*)>(?<content>.*?)</td>')
    if ($CellMatches.Count -lt 3) {
        return $Row
    }

    $TrackCell = $CellMatches[2]
    $CleanTrack = Remove-ChineseText $TrackCell.Groups["content"].Value
    $Replacement = "<td$($TrackCell.Groups["attrs"].Value)>$CleanTrack</td>"
    return $Row.Substring(0, $TrackCell.Index) + $Replacement + $Row.Substring($TrackCell.Index + $TrackCell.Length)
}

function Write-StatusBarSvg {
    param(
        [array]$ActiveStatuses,
        [hashtable]$Counts
    )

    $Total = 0
    foreach ($Status in $ActiveStatuses) {
        $Total += $Counts[$Status.Name]
    }

    $MaxValue = ($ActiveStatuses | ForEach-Object { $Counts[$_.Name] } | Measure-Object -Maximum).Maximum
    if ($null -eq $MaxValue -or $MaxValue -lt 10) {
        $MaxValue = 10
    }
    $MaxAxis = [int]([math]::Ceiling($MaxValue / 10) * 10)
    $Bottom = 318
    $Top = 78
    $Height = $Bottom - $Top
    $Scale = $Height / $MaxAxis
    $BarWidth = 80
    $FirstX = 116
    $StepX = 160

    $Desc = ($ActiveStatuses | ForEach-Object { "$($_.Name)$($Counts[$_.Name])" }) -join "，"
    $Grid = New-Object System.Collections.Generic.List[string]
    for ($Tick = 0; $Tick -le $MaxAxis; $Tick += 10) {
        $Y = [int][math]::Round($Bottom - ($Tick * $Scale))
        $Stroke = if ($Tick -eq 0) { "#d1d5db" } else { "#e5e7eb" }
        $Grid.Add("    <line x1=""64"" y1=""$Y"" x2=""720"" y2=""$Y"" stroke=""$Stroke"" stroke-width=""1""/>")
    }
    for ($Tick = 0; $Tick -le $MaxAxis; $Tick += 10) {
        $Y = [int][math]::Round($Bottom - ($Tick * $Scale) + 4)
        $Grid.Add("    <text x=""42"" y=""$Y"" text-anchor=""end"">$Tick</text>")
    }

    $Bars = New-Object System.Collections.Generic.List[string]
    $Labels = New-Object System.Collections.Generic.List[string]
    for ($i = 0; $i -lt $ActiveStatuses.Count; $i++) {
        $Status = $ActiveStatuses[$i]
        $Count = [int]$Counts[$Status.Name]
        $BarHeight = [int][math]::Round($Count * $Scale)
        if ($Count -gt 0 -and $BarHeight -lt 5) {
            $BarHeight = 5
        }
        $Y = $Bottom - $BarHeight
        $X = $FirstX + ($i * $StepX)
        $TextX = $X + ($BarWidth / 2)
        $TextY = $Y - 8
        $Bars.Add("    <rect x=""$X"" y=""$Y"" width=""$BarWidth"" height=""$BarHeight"" rx=""4"" fill=""$($Status.Fill)"" stroke=""$($Status.Stroke)""/>")
        $Bars.Add("    <text x=""$TextX"" y=""$TextY"" fill=""#111827"">$Count</text>")
        $Labels.Add("    <text x=""$TextX"" y=""346"">$($Status.Name)</text>")
    }

    $Svg = @"
<svg xmlns="http://www.w3.org/2000/svg" width="760" height="430" viewBox="0 0 760 430" role="img" aria-labelledby="title desc">
  <title id="title">论文状态统计柱状图</title>
  <desc id="desc">$Desc。</desc>
  <rect width="760" height="430" fill="#ffffff"/>
  <text x="30" y="34" fill="#111827" font-family="Arial, Microsoft YaHei, sans-serif" font-size="22" font-weight="700">论文状态统计</text>
  <text x="30" y="58" fill="#6b7280" font-family="Arial, Microsoft YaHei, sans-serif" font-size="13">共 $Total 篇/项；已接收论文不纳入统计</text>

  <g font-family="Arial, Microsoft YaHei, sans-serif" font-size="12" fill="#6b7280">
$($Grid -join $NewLine)
  </g>

  <g font-family="Arial, Microsoft YaHei, sans-serif" font-size="14" font-weight="700" text-anchor="middle">
$($Bars -join ($NewLine + $NewLine))
  </g>

  <g font-family="Arial, Microsoft YaHei, sans-serif" font-size="12" fill="#374151" text-anchor="middle">
$($Labels -join $NewLine)
  </g>
</svg>
"@

    [System.IO.File]::WriteAllText($SvgPath, $Svg, $Utf8NoBom)
}

$Readme = [System.IO.File]::ReadAllText($ReadmePath, $Utf8NoBom)
$BodyMatch = [regex]::Match($Readme, '(?s)(<tbody>\s*)(.*?)(\s*</tbody>)')
if (-not $BodyMatch.Success) {
    throw "README.md 中没有找到论文状态表 <tbody>。"
}

$Rows = [regex]::Matches($BodyMatch.Groups[2].Value, '(?s)<tr bgcolor="#[0-9A-Fa-f]{6}" style="background-color:#[0-9A-Fa-f]{6};?">.*?</tr>')
if ($Rows.Count -eq 0) {
    throw "README.md 中没有找到可排序的论文状态行。"
}

$ParsedRows = New-Object System.Collections.Generic.List[object]
for ($i = 0; $i -lt $Rows.Count; $i++) {
    $Row = $Rows[$i].Value
    $Status = Get-StatusFromRow $Row
    if (-not $Status) {
        throw "第 $($i + 1) 个论文状态行没有找到状态单元格。"
    }

    if (-not $StatusByName.ContainsKey($Status)) {
        throw "发现未知状态：$Status"
    }

    $ParsedRows.Add([pscustomobject]@{
        Index = $i
        Status = $Status
        Row = Normalize-StatusRow $Row $Status
    })
}

$SortedRows = $ParsedRows |
    Sort-Object @{ Expression = { $StatusByName[$_.Status].Order }; Ascending = $true }, @{ Expression = { $_.Index }; Ascending = $true }
$NewBody = ($SortedRows | ForEach-Object { $_.Row }) -join ($NewLine + $NewLine)
$Readme = $Readme.Substring(0, $BodyMatch.Groups[2].Index) + $NewBody + $Readme.Substring($BodyMatch.Groups[2].Index + $BodyMatch.Groups[2].Length)

$Counts = @{}
foreach ($Status in $Statuses) {
    $Counts[$Status.Name] = 0
}
foreach ($Row in $SortedRows) {
    $Counts[$Row.Status]++
}
$TotalCount = ($Counts.Values | Measure-Object -Sum).Sum
$ActiveStatuses = $Statuses | Where-Object { $Counts[$_.Name] -gt 0 }

$LegendRows = ($Statuses | ForEach-Object {
    "<tr><td>$($_.Icon)</td><td>$($_.Name)</td></tr>"
}) -join $NewLine
$Legend = "<table width=""100%"">$NewLine$LegendRows$NewLine</table>"
$Readme = [regex]::Replace($Readme, '(?s)(## 颜色图例\s*)<table width="100%">.*?</table>', "`${1}$Legend", 1)

$MaintenanceRule = '> **维护规则：** 本仓库已启用提交前自动排序；修改论文状态后，pre-commit 会运行 `pwsh -File scripts/Update-PaperStatus.ps1` 并同步 README 和图表，GitHub Actions 会在推送后再次兜底规范化。'
if ($Readme -match [regex]::Escape("> **维护规则：**")) {
    $Readme = [regex]::Replace($Readme, '(?m)^> \*\*维护规则：\*\*.*$', [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $MaintenanceRule }, 1)
}
else {
    $Readme = $Readme.Replace(
        "> **说明：** 待投稿包含所有未处于投稿流程中的论文；已接收论文不再纳入本表统计。状态列用彩色圆点区分。",
        "> **说明：** 待投稿包含所有未处于投稿流程中的论文；已接收论文不再纳入本表统计。状态列用彩色圆点区分。$NewLine$NewLine$MaintenanceRule"
    )
}

$StatRows = ($Statuses | ForEach-Object {
    $Count = $Counts[$_.Name]
    "<tr bgcolor=""$($_.Fill)"" style=""background-color:$($_.Fill);""><td>$($_.Icon) $($_.Name)</td><td>$Count</td></tr>"
}) -join $NewLine
$Readme = [regex]::Replace(
    $Readme,
    '(?s)(<tr><th>状态</th><th>数量</th></tr>\s*).*?(\s*<tr><td><strong>合计</strong></td><td><strong>)\d+(</strong></td></tr>)',
    "`${1}$StatRows`${2}$TotalCount`${3}",
    1
)

[System.IO.File]::WriteAllText($ReadmePath, $Readme, $Utf8NoBom)

$Chart = [System.IO.File]::ReadAllText($ChartHtmlPath, $Utf8NoBom)
$LabelLines = ($ActiveStatuses | ForEach-Object { "      ""$($_.Name)""" }) -join ",$NewLine"
$ValueLine = ($ActiveStatuses | ForEach-Object { $Counts[$_.Name] }) -join ", "
$ColorLines = ($ActiveStatuses | ForEach-Object { "      ""$($_.Fill)""" }) -join ",$NewLine"
$StrokeLines = ($ActiveStatuses | ForEach-Object { "      ""$($_.Stroke)""" }) -join ",$NewLine"
$Chart = [regex]::Replace($Chart, '(?s)    const labels = \[.*?\];', "    const labels = [$NewLine$LabelLines$NewLine    ];", 1)
$Chart = [regex]::Replace($Chart, '    const values = \[[^\]]*\];', "    const values = [$ValueLine];", 1)
$Chart = [regex]::Replace($Chart, '(?s)    const colors = \[.*?\];', "    const colors = [$NewLine$ColorLines$NewLine    ];", 1)
$Chart = [regex]::Replace($Chart, '(?s)    const markerLines = \[.*?\];', "    const markerLines = [$NewLine$StrokeLines$NewLine    ];", 1)
[System.IO.File]::WriteAllText($ChartHtmlPath, $Chart, $Utf8NoBom)

Write-StatusBarSvg $ActiveStatuses $Counts
