Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ReadmePath = Join-Path $RepoRoot "README.md"
$ChartHtmlPath = Join-Path $RepoRoot "status_chart.html"
$SvgPath = Join-Path $RepoRoot "status_bar_chart.svg"
$IndexPath = Join-Path $RepoRoot "index.html"
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$NewLine = "`n"

$Statuses = @(
    [pscustomobject]@{ Name = "待投稿"; Icon = "&#9898;"; Fill = "#f2f2f2"; Stroke = "#9ca3af"; ChartFill = "#64748b" },
    [pscustomobject]@{ Name = "需修订"; Icon = "&#128150;"; Fill = "#ffd9ec"; Stroke = "#ec4899"; ChartFill = "#f43f5e" },
    [pscustomobject]@{ Name = "内审中"; Icon = "&#128993;"; Fill = "#fff8d9"; Stroke = "#eab308"; ChartFill = "#f59e0b" },
    [pscustomobject]@{ Name = "外审中"; Icon = "&#128994;"; Fill = "#e8f9ee"; Stroke = "#22c55e"; ChartFill = "#22c55e" }
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

function Get-PiePoint {
    param(
        [double]$CenterX,
        [double]$CenterY,
        [double]$Radius,
        [double]$Angle
    )

    $Radians = ($Angle - 90) * [math]::PI / 180
    return [pscustomobject]@{
        X = [math]::Round($CenterX + ($Radius * [math]::Cos($Radians)), 3)
        Y = [math]::Round($CenterY + ($Radius * [math]::Sin($Radians)), 3)
    }
}

function Write-StatusPieSvg {
    param(
        [array]$ActiveStatuses,
        [hashtable]$Counts
    )

    $Total = 0
    foreach ($Status in $ActiveStatuses) {
        $Total += $Counts[$Status.Name]
    }

    $Desc = ($ActiveStatuses | ForEach-Object { "$($_.Name)$($Counts[$_.Name])" }) -join "，"
    $CenterX = 258
    $CenterY = 232
    $Radius = 132
    $Slices = New-Object System.Collections.Generic.List[string]
    $Legend = New-Object System.Collections.Generic.List[string]
    $Angle = 0.0
    for ($i = 0; $i -lt $ActiveStatuses.Count; $i++) {
        $Status = $ActiveStatuses[$i]
        $Count = [int]$Counts[$Status.Name]
        if ($Count -le 0) {
            continue
        }
        $Sweep = 360 * $Count / $Total
        $Start = Get-PiePoint $CenterX $CenterY $Radius $Angle
        $EndAngle = $Angle + $Sweep
        $End = Get-PiePoint $CenterX $CenterY $Radius $EndAngle
        $LargeArc = if ($Sweep -gt 180) { 1 } else { 0 }
        $Slices.Add("    <path d=""M $CenterX $CenterY L $($Start.X) $($Start.Y) A $Radius $Radius 0 $LargeArc 1 $($End.X) $($End.Y) Z"" fill=""$($Status.ChartFill)"" stroke=""#ffffff"" stroke-width=""3""/>")

        $LabelAngle = $Angle + ($Sweep / 2)
        $LabelPoint = Get-PiePoint $CenterX $CenterY 82 $LabelAngle
        $Percent = [math]::Round(($Count / $Total) * 100, 1)
        if ($Percent -ge 5) {
            $Slices.Add("    <text x=""$($LabelPoint.X)"" y=""$($LabelPoint.Y)"" fill=""#ffffff"" font-size=""15"" font-weight=""700"" text-anchor=""middle"" dominant-baseline=""middle"">$Percent%</text>")
        }

        $LegendY = 128 + ($i * 58)
        $Legend.Add("    <rect x=""492"" y=""$($LegendY - 18)"" width=""24"" height=""24"" rx=""5"" fill=""$($Status.ChartFill)""/>")
        $Legend.Add("    <text x=""528"" y=""$($LegendY - 2)"" fill=""#111827"" font-size=""15"" font-weight=""700"">$($Status.Name)</text>")
        $Legend.Add("    <text x=""528"" y=""$($LegendY + 20)"" fill=""#4b5563"" font-size=""13"">$Count 篇，占比 $Percent%</text>")
        $Angle = $EndAngle
    }

    $Svg = @"
<svg xmlns="http://www.w3.org/2000/svg" width="760" height="430" viewBox="0 0 760 430" role="img" aria-labelledby="title desc">
  <title id="title">论文状态统计饼图</title>
  <desc id="desc">$Desc。</desc>
  <rect width="760" height="430" fill="#ffffff"/>
  <text x="30" y="34" fill="#111827" font-family="Arial, Microsoft YaHei, sans-serif" font-size="22" font-weight="700">论文状态统计</text>
  <text x="30" y="58" fill="#6b7280" font-family="Arial, Microsoft YaHei, sans-serif" font-size="13">共 $Total 篇/项；已接收论文不纳入统计</text>

  <g font-family="Arial, Microsoft YaHei, sans-serif">
$($Slices -join $NewLine)
    <circle cx="$CenterX" cy="$CenterY" r="58" fill="#ffffff"/>
    <text x="$CenterX" y="$($CenterY - 8)" fill="#6b7280" font-size="13" font-weight="700" text-anchor="middle">总计</text>
    <text x="$CenterX" y="$($CenterY + 22)" fill="#111827" font-size="28" font-weight="700" text-anchor="middle">$Total</text>
  </g>

  <g font-family="Arial, Microsoft YaHei, sans-serif">
$($Legend -join $NewLine)
  </g>
</svg>
"@

    [System.IO.File]::WriteAllText($SvgPath, $Svg, $Utf8NoBom)
}

function Write-IndexPage {
    param(
        [array]$ActiveStatuses,
        [hashtable]$Counts,
        [string]$Readme
    )

    $Total = 0
    foreach ($Status in $ActiveStatuses) {
        $Total += $Counts[$Status.Name]
    }

    $SummaryCards = ($ActiveStatuses | ForEach-Object {
        $Count = $Counts[$_.Name]
        $Percent = [math]::Round(($Count / $Total) * 100, 1)
        @"
        <article class="stat-card" style="--accent:$($_.ChartFill)">
          <span class="dot">$($_.Icon)</span>
          <div>
            <strong>$Count</strong>
            <span>$($_.Name) · $Percent%</span>
          </div>
        </article>
"@
    }) -join $NewLine

    $LegendRows = ($ActiveStatuses | ForEach-Object {
        "<tr><td>$($_.Icon)</td><td>$($_.Name)</td><td>$($Counts[$_.Name])</td></tr>"
    }) -join $NewLine

    $PaperTableMatch = [regex]::Match($Readme, '(?s)<table class="paper-status-table".*?</table>')
    if (-not $PaperTableMatch.Success) {
        throw "README.md 中没有找到论文状态总表。"
    }
    $PaperTable = [regex]::Replace($PaperTableMatch.Value, '(?s)\s*<!--.*?-->', '')

    $Html = @"
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>全部论文投稿状态</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f8fafc;
      --panel: #ffffff;
      --text: #111827;
      --muted: #64748b;
      --line: #e5e7eb;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      color: var(--text);
      background: var(--bg);
    }

    main {
      max-width: 1500px;
      margin: 0 auto;
      padding: 24px;
    }

    header {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }

    h1 {
      margin: 0;
      font-size: 28px;
      letter-spacing: 0;
    }

    .updated {
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }

    .summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }

    .stat-card {
      display: flex;
      align-items: center;
      gap: 12px;
      min-height: 72px;
      padding: 12px 14px;
      border: 1px solid var(--line);
      border-left: 8px solid var(--accent);
      border-radius: 8px;
      background: var(--panel);
    }

    .dot { font-size: 22px; line-height: 1; }

    .stat-card strong {
      display: block;
      font-size: 24px;
      line-height: 1.1;
    }

    .stat-card span:last-child {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 13px;
    }

    .dashboard {
      display: grid;
      grid-template-columns: minmax(320px, 2fr) minmax(220px, 0.8fr);
      gap: 14px;
      align-items: stretch;
      margin-bottom: 18px;
    }

    .panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      overflow: hidden;
    }

    .chart-panel {
      padding: 12px;
    }

    .chart-panel img {
      display: block;
      width: 100%;
      height: auto;
    }

    .legend-panel {
      padding: 14px;
    }

    .legend-panel h2,
    .table-panel h2 {
      margin: 0 0 12px;
      font-size: 18px;
    }

    .legend-panel table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }

    .legend-panel td {
      padding: 9px 8px;
      border-bottom: 1px solid var(--line);
    }

    .table-panel {
      padding: 14px;
      overflow-x: auto;
    }

    table.paper-status-table {
      width: 100%;
      min-width: 1160px;
      border-collapse: collapse;
      table-layout: auto;
      font-size: 14px;
    }

    table.paper-status-table th,
    table.paper-status-table td {
      padding: 9px 10px;
      border: 1px solid var(--line);
      vertical-align: top;
    }

    table.paper-status-table th:nth-child(1),
    table.paper-status-table td:nth-child(1) {
      width: 6%;
      min-width: 48px;
      text-align: center;
      white-space: nowrap;
    }

    table.paper-status-table th:nth-child(2),
    table.paper-status-table td:nth-child(2) {
      width: 49%;
      min-width: 520px;
    }

    table.paper-status-table th:nth-child(3),
    table.paper-status-table td:nth-child(3) {
      width: 45%;
      min-width: 540px;
    }

    @media (max-width: 900px) {
      main { padding: 16px; }
      header { display: block; }
      .updated { display: block; margin-top: 8px; }
      .dashboard { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>全部论文投稿状态</h1>
      <span class="updated">最后更新：2026-05-07</span>
    </header>

    <section class="summary">
$SummaryCards
    </section>

    <section class="dashboard">
      <div class="panel chart-panel">
        <img src="status_bar_chart.svg" alt="论文状态统计饼图">
      </div>
      <aside class="panel legend-panel">
        <h2>颜色图例</h2>
        <table>
          <tbody>
$LegendRows
          </tbody>
        </table>
      </aside>
    </section>

    <section class="panel table-panel">
      <h2>全部论文状态总表</h2>
$PaperTable
    </section>
  </main>
</body>
</html>
"@

    [System.IO.File]::WriteAllText($IndexPath, $Html, $Utf8NoBom)
}

$Readme = [System.IO.File]::ReadAllText($ReadmePath, $Utf8NoBom)
$Readme = [regex]::Replace($Readme, '(?s)\s*<style>.*?</style>\s*', "$NewLine$NewLine", 1)
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

$Readme = [regex]::Replace($Readme, '(?m)^> \*\*说明：\*\*.*\r?\n?', '', 1)
$Readme = [regex]::Replace($Readme, '(?m)^> \*\*维护规则：\*\*.*\r?\n?', '', 1)
$Readme = $Readme.Replace('alt="状态统计柱状图"', 'alt="状态统计饼图"')
if ($Readme -notmatch '\[打开网页状态面板\]\(index\.html\)') {
    $Readme = $Readme.Replace(
        '[查看 Plotly 状态统计图](status_chart.html)',
        "[打开网页状态面板](index.html)$NewLine$NewLine[查看 Plotly 状态统计图](status_chart.html)"
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
$ColorLines = ($ActiveStatuses | ForEach-Object { "      ""$($_.ChartFill)""" }) -join ",$NewLine"
$StrokeLines = ($ActiveStatuses | ForEach-Object { "      ""$($_.Stroke)""" }) -join ",$NewLine"
$Chart = [regex]::Replace($Chart, '(?s)    const labels = \[.*?\];', "    const labels = [$NewLine$LabelLines$NewLine    ];", 1)
$Chart = [regex]::Replace($Chart, '    const values = \[[^\]]*\];', "    const values = [$ValueLine];", 1)
$Chart = [regex]::Replace($Chart, '(?s)    const colors = \[.*?\];', "    const colors = [$NewLine$ColorLines$NewLine    ];", 1)
$Chart = [regex]::Replace($Chart, '(?s)    const markerLines = \[.*?\];', "    const markerLines = [$NewLine$StrokeLines$NewLine    ];", 1)
[System.IO.File]::WriteAllText($ChartHtmlPath, $Chart, $Utf8NoBom)

Write-StatusPieSvg $ActiveStatuses $Counts
Write-IndexPage $ActiveStatuses $Counts $Readme
