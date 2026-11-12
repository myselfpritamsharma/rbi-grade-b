param(
    [Parameter(Mandatory = $true)][string]$Video,
    [string]$OutputDirectory = 'recording-export',
    [switch]$Inspect,
    [double]$IntervalSeconds = 0.5,
    [string]$Crop = '1170:968:377:0',
    [double]$LimitSeconds = 0,
    [switch]$ReuseFrames,
    [switch]$BuildOnly
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Storage.FileAccessMode, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrResult, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1

function Wait-WinRt($Operation, [Type]$ResultType) {
    $task = $asTask.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
    return $task.GetAwaiter().GetResult()
}

function Read-ImageText([string]$Path) {
    $file = Wait-WinRt ([Windows.Storage.StorageFile]::GetFileFromPathAsync($Path)) ([Windows.Storage.StorageFile])
    $stream = Wait-WinRt ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    try {
        $decoder = Wait-WinRt ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = Wait-WinRt ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        try {
            $result = Wait-WinRt ($ocr.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
            return ($result.Lines | ForEach-Object { $_.Text }) -join "`n"
        } finally { $bitmap.Dispose() }
    } finally { $stream.Dispose() }
}

function Invoke-VideoExtraction([string[]]$Arguments) {
    $processInfo = New-Object Diagnostics.ProcessStartInfo
    $processInfo.FileName = $ffmpegPath
    $processInfo.Arguments = ($Arguments | ForEach-Object { '"' + $_.Replace('"', '\"') + '"' }) -join ' '
    $processInfo.UseShellExecute = $false
    $processInfo.CreateNoWindow = $true
    $processInfo.RedirectStandardError = $true
    $process = [Diagnostics.Process]::Start($processInfo)
    $log = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    $exitCode = $process.ExitCode
    $process.Dispose()
    if ($exitCode -ne 0) { throw "FFmpeg failed: $log" }
    return $log
}

function Encode-Html([string]$Text) { return [Net.WebUtility]::HtmlEncode($Text) }

function Write-RecordingHtml($Captures, [string]$Path) {
    $topicPatterns = [ordered]@{
        'General Awareness' = '(?im)^\s*GENERAL AWARENESS(?:\s*[|I]?\s*\d*)?\s*$'
        'Reasoning' = '(?im)^\s*REASONING(?:\s*[|I]?\s*\d*)?\s*$'
        'English Language' = '(?im)^\s*ENGLISH LANGUAGE(?:\s*[|I]?\s*\d*)?\s*$'
        'Quantitative Aptitude' = '(?im)^\s*QUANTITATIVE APTITUDE(?:\s*[|I]?\s*\d*)?\s*$'
    }
    $groups = [ordered]@{}
    $questionScreens = @{}
    $currentTopic = 'Front Matter / Review'
    foreach ($capture in $Captures) {
        $seenTopics = @($topicPatterns.GetEnumerator() | Where-Object { [regex]::IsMatch($capture.text, $_.Value) } | ForEach-Object { $_.Key })
        if ($seenTopics.Count -eq 1) { $currentTopic = $seenTopics[0] }
        elseif ($seenTopics.Count -gt 1) { $currentTopic = 'Mixed / Review' }
        if (-not $groups.Contains($currentTopic)) { $groups[$currentTopic] = New-Object 'Collections.Generic.List[object]' }

        $questionNumberSet = New-Object 'Collections.Generic.SortedSet[int]'
        foreach ($match in [regex]::Matches($capture.text, '(?im)^\s*[QO]\s*[.\-:]?\s*([0-9IlOoSs]{1,3})\s*[).]?')) {
            $digits = $match.Groups[1].Value.Replace('I', '1').Replace('l', '1').Replace('O', '0').Replace('o', '0').Replace('S', '5').Replace('s', '5')
            $number = 0
            if ([int]::TryParse($digits, [ref]$number) -and $number -ge 1 -and $number -le 200) {
                $null = $questionNumberSet.Add($number)
                if (-not $questionScreens.ContainsKey($number)) { $questionScreens[$number] = $capture.index }
            }
        }
        $questions = @($questionNumberSet)
        $groups[$currentTopic].Add([pscustomobject]@{capture = $capture; questions = $questions})
    }

    $document = New-Object Text.StringBuilder
    $null = $document.Append(@'
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RBI Phase 1 2025 - Source Reader</title>
<style>
:root{--ink:#24221e;--muted:#69645b;--line:#d8d1c5;--paper:#f5f1e8;--sheet:#fffefa;--accent:#315f52;--wash:#e8e1d4}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--ink);background:var(--paper);font:17px/1.6 Georgia,'Times New Roman',serif}
header{background:var(--sheet);border-bottom:1px solid var(--line);padding:28px max(24px,calc((100vw - 1180px)/2)) 22px}
main{max-width:1180px;margin:0 auto;padding:24px}
h1{font-size:32px;line-height:1.2;margin:0 0 8px}h2{font-size:25px;line-height:1.25;margin:0 0 4px}
p{color:var(--muted);margin:8px 0 14px}.eyebrow,.meta{font:13px/1.4 Arial,sans-serif;letter-spacing:0;color:var(--muted)}
.controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:18px}.controls label{font:14px Arial,sans-serif}
input{width:min(100%,360px);padding:10px 12px;border:1px solid var(--line);background:#fff;font:16px Arial,sans-serif;color:var(--ink)}
nav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 0}nav a,.index a{color:var(--accent)}nav a{font:14px Arial,sans-serif;text-decoration:none;padding:6px 10px;border:1px solid var(--line);background:var(--sheet)}
details{border-top:1px solid var(--line)}summary{cursor:pointer;color:var(--accent);padding:12px 0;font:15px Arial,sans-serif}
.index{margin:18px 0 30px;background:var(--sheet);padding:16px 20px;border:1px solid var(--line)}.index-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:0 16px}
.index a,.index .missing{display:flex;justify-content:space-between;gap:8px;padding:5px 0;border-bottom:1px solid var(--wash);font:14px/1.4 Arial,sans-serif;text-decoration:none}
.index .missing{color:var(--muted)}.topic{margin:34px 0 44px;scroll-margin-top:16px}.topic-head{border-bottom:2px solid var(--ink);padding-bottom:10px;margin-bottom:8px}
.source-page{margin:0;border-bottom:1px solid var(--line);scroll-margin-top:12px}.source-page summary{display:flex;justify-content:space-between;align-items:center;gap:12px;color:var(--ink);padding:13px 10px;background:rgba(255,254,250,.55)}
.source-page summary:hover{background:var(--sheet)}.page{margin:0 auto;padding:12px 16px 24px;max-width:1060px;background:var(--sheet)}
.page img{display:block;width:100%;height:auto;border:1px solid var(--line);background:#fff}.caption{display:flex;justify-content:space-between;gap:12px;margin:0 0 10px;font:13px Arial,sans-serif;color:var(--muted)}
[hidden]{display:none!important}
@media(max-width:600px){header{padding:22px 18px 18px}main{padding:16px}h1{font-size:27px}.index{padding:12px}.index-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.source-page summary{align-items:flex-start;flex-direction:column;gap:2px}.page{padding:8px 0 16px}}
@media print{body{background:#fff}header{padding:0 0 14px}main{padding:0}.controls,nav,.index{display:none}.topic{break-before:page}.source-page{break-inside:avoid}.source-page>summary{display:none}.page{display:block!important;padding:0}.page img{border:0}}
</style></head><body><header><h1>RBI Phase 1 2025</h1>
<div class="eyebrow">Recorded source reader</div>
<p>Read the original captured pages by section. Every saved screen is included; question links are added when OCR can identify a number. Unclear labels are marked for checking in the source pages.</p>
<div class="controls"><label for="search">Find a question number or section</label><input id="search" type="search" placeholder="For example: 120 or reasoning"><span id="count" class="meta"></span></div>
'@)
    $null = $document.Append('<nav aria-label="Topics">')
    foreach ($topic in $groups.Keys) {
        $slug = [regex]::Replace($topic.ToLowerInvariant(), '[^a-z0-9]+', '-')
        $null = $document.Append('<a href="#topic-' + $slug + '">' + (Encode-Html $topic) + ' (' + $groups[$topic].Count + ')</a>')
    }
    $null = $document.Append('</nav></header><main><details class="index" open><summary>Question index - 1 to 200</summary><div class="index-grid">')
    for ($number = 1; $number -le 200; $number++) {
        if ($questionScreens.ContainsKey($number)) {
            $screen = $questionScreens[$number]
            $null = $document.Append('<a href="#screen-' + $screen + '"><span>Question ' + $number + '</span><span>Screen ' + $screen + '</span></a>')
        } else {
            $null = $document.Append('<a class="missing" href="#all-source-pages"><span>Question ' + $number + '</span><span>Check source</span></a>')
        }
    }
    $null = $document.Append('</div></details><div id="all-source-pages">')
    foreach ($topic in $groups.Keys) {
        $slug = [regex]::Replace($topic.ToLowerInvariant(), '[^a-z0-9]+', '-')
        $null = $document.Append('<section class="topic" id="topic-' + $slug + '"><div class="topic-head"><div class="eyebrow">' + $groups[$topic].Count + ' captured screens</div><h2>' + (Encode-Html $topic) + '</h2></div>')
        foreach ($entry in $groups[$topic]) {
            $capture = $entry.capture
            $stamp = [TimeSpan]::FromSeconds($capture.seconds).ToString('mm\:ss\.f')
            $picture = [Convert]::ToBase64String([IO.File]::ReadAllBytes($capture.image))
            if ($entry.questions.Count -gt 0) {
                $questionLabel = 'Question ' + (($entry.questions | ForEach-Object { $_ }) -join ', ')
            } else {
                $questionLabel = 'Question number unclear'
            }
            $searchParts = New-Object 'Collections.Generic.List[string]'
            $searchParts.Add($topic)
            foreach ($question in $entry.questions) {
                $searchParts.Add('question ' + $question)
                $searchParts.Add([string]$question)
            }
            $searchText = [Net.WebUtility]::HtmlEncode(([string]::Join(' ', $searchParts)).ToLowerInvariant())
            $null = $document.Append('<details class="source-page" id="screen-' + $capture.index + '" data-search="' + $searchText + '"><summary><span>Screen ' + $capture.index.ToString('00000') + '</span><span class="meta">Recording ' + $stamp + ' - ' + (Encode-Html $questionLabel) + '</span></summary><figure class="page"><figcaption class="caption"><span>' + (Encode-Html $topic) + '</span><span>Recording ' + $stamp + '</span></figcaption><img loading="lazy" alt="Source recording screen ' + $capture.index + '" src="data:image/jpeg;base64,' + $picture + '"></figure></details>')
        }
        $null = $document.Append('</section>')
    }
    $null = $document.Append('</div></main><script>')
    $null = $document.Append(@'
const pages=[...document.querySelectorAll('.source-page')];
const search=document.querySelector('#search');
function filter(){const query=search.value.toLowerCase().trim();const exactNumber=/^\d+$/.test(query);let visible=0;pages.forEach(page=>{const tokens=page.dataset.search.split(/\s+/);page.hidden=exactNumber?!tokens.includes(query):!page.dataset.search.includes(query);if(!page.hidden)visible++});document.querySelector('#count').textContent=visible+' of '+pages.length+' screens'}
search.addEventListener('input',filter);filter();
document.querySelectorAll('a[href^="#screen-"]').forEach(link=>link.addEventListener('click',()=>{search.value='';filter();const page=document.querySelector(link.getAttribute('href'));if(page)page.open=true}));
</script></body></html>
'@)
    [IO.File]::WriteAllText($Path, $document.ToString(), (New-Object Text.UTF8Encoding($false)))
}

$videoPath = (Resolve-Path -LiteralPath $Video).Path
$outputPath = [IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputDirectory))
$null = New-Item -ItemType Directory -Force -Path $outputPath
if ($BuildOnly) {
    $captures = Get-Content -LiteralPath (Join-Path $outputPath 'captures.json') -Raw | ConvertFrom-Json
    Write-RecordingHtml $captures (Join-Path $outputPath 'questions-answers.html')
    Write-Host ('Rebuilt HTML from {0} saved screens.' -f $captures.Count)
    return
}
$cache = Join-Path $env:LOCALAPPDATA 'RBI-Recording-Exporter'
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpeg) {
    $ffmpegPath = $ffmpeg.Source
    $ffprobePath = (Get-Command ffprobe -ErrorAction Stop).Source
} else {
    $ffmpegPath = Get-ChildItem -LiteralPath $cache -Filter ffmpeg.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
    if (-not $ffmpegPath) {
        $null = New-Item -ItemType Directory -Force -Path $cache
        $archive = Join-Path $cache 'ffmpeg.zip'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Write-Host 'Downloading portable FFmpeg from gyan.dev (no system installation).'
        try {
            Invoke-WebRequest 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile $archive -UseBasicParsing
        } catch {
            Write-Host 'Primary server unavailable; trying the publisher GitHub release.'
            $release = Invoke-RestMethod 'https://api.github.com/repos/GyanD/codexffmpeg/releases/latest'
            $asset = $release.assets | Where-Object name -like '*essentials_build.zip' | Select-Object -First 1
            if (-not $asset) { throw 'No portable FFmpeg ZIP found in the release.' }
            Invoke-WebRequest $asset.browser_download_url -OutFile $archive -UseBasicParsing
        }
        Expand-Archive -LiteralPath $archive -DestinationPath $cache -Force
        Remove-Item -LiteralPath $archive
        $ffmpegPath = Get-ChildItem -LiteralPath $cache -Filter ffmpeg.exe -Recurse | Select-Object -First 1 -ExpandProperty FullName
    }
    $ffprobePath = Join-Path (Split-Path $ffmpegPath) 'ffprobe.exe'
}

$ocr = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (-not $ocr) { throw 'Windows OCR has no available language. Install an English language OCR pack in Windows Settings.' }
$metadata = (& $ffprobePath -v error -show_format -show_streams -of json $videoPath) -join "`n" | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'FFprobe could not read the recording.' }
$duration = [double]::Parse($metadata.format.duration, [Globalization.CultureInfo]::InvariantCulture)
$videoStream = $metadata.streams | Where-Object codec_type -eq 'video' | Select-Object -First 1
Write-Host ('Duration: {0:N1}s; size: {1}x{2}; OCR: {3}' -f $duration, $videoStream.width, $videoStream.height, $ocr.RecognizerLanguage.LanguageTag)
$preview = Join-Path $outputPath 'preview.jpg'
$time = ($duration * 0.1).ToString('0.###', [Globalization.CultureInfo]::InvariantCulture)
& $ffmpegPath -hide_banner -loglevel error -y -ss $time -i $videoPath -frames:v 1 $preview
if ($LASTEXITCODE -ne 0) { throw 'Could not extract preview frame.' }
Write-Host "Preview: $preview"
Write-Host (Read-ImageText $preview)
if ($Inspect) { return }
if ($IntervalSeconds -le 0) { throw 'IntervalSeconds must be positive.' }
$framesPath = Join-Path $outputPath 'frames'
if ($ReuseFrames) {
    $log = [IO.File]::ReadAllText((Join-Path $outputPath 'frames.log'))
} else {
    if (Test-Path -LiteralPath $framesPath) { throw 'This output already contains frames. Use a fresh OutputDirectory or ReuseFrames.' }
    $null = New-Item -ItemType Directory -Path $framesPath
    $rate = (1.0 / $IntervalSeconds).ToString('0.######', [Globalization.CultureInfo]::InvariantCulture)
    $filter = "fps=$rate"
    if ($Crop) { $filter += ",crop=$Crop" }
    $filter += ',mpdecimate,showinfo'
    $arguments = @('-hide_banner', '-y', '-i', $videoPath)
    if ($LimitSeconds -gt 0) { $arguments += @('-t', $LimitSeconds.ToString('0.###', [Globalization.CultureInfo]::InvariantCulture)) }
    $arguments += @('-an', '-vf', $filter, '-fps_mode', 'vfr', '-q:v', '3', (Join-Path $framesPath 'screen-%05d.jpg'))
    Write-Host 'Extracting changed screens from the recording...'
    $log = Invoke-VideoExtraction $arguments
    [IO.File]::WriteAllText((Join-Path $outputPath 'frames.log'), $log)
}
$timestamps = @([regex]::Matches($log, 'pts_time:([\d.]+)') | ForEach-Object {
    [double]::Parse($_.Groups[1].Value, [Globalization.CultureInfo]::InvariantCulture)
} | Where-Object { $LimitSeconds -le 0 -or $_ -lt $LimitSeconds })
$frames = @(Get-ChildItem -LiteralPath $framesPath -Filter 'screen-*.jpg' | Sort-Object Name)
if ($frames.Count -eq 0 -or $frames.Count -ne $timestamps.Count) { throw 'Frame extraction did not produce matching images and timestamps.' }
$captures = New-Object 'Collections.Generic.List[object]'
$previous = ''
for ($index = 0; $index -lt $frames.Count; $index++) {
    $text = Read-ImageText $frames[$index].FullName
    $normalized = ($text.ToLowerInvariant() -replace '\s+', ' ').Trim()
    if ($normalized.Length -gt 25 -and $normalized -ne $previous) {
        $captures.Add([pscustomobject]@{index = $captures.Count + 1; seconds = $timestamps[$index]; text = $text; image = $frames[$index].FullName})
        $previous = $normalized
    }
    if (($index + 1) % 25 -eq 0 -or $index -eq $frames.Count - 1) {
        Write-Host ('OCR: {0}/{1} frames; {2} text screens retained' -f ($index + 1), $frames.Count, $captures.Count)
        $captures | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $outputPath 'captures.json') -Encoding UTF8
    }
}
if ($captures.Count -eq 0) { throw 'No readable text was found.' }
$htmlPath = Join-Path $outputPath 'questions-answers.html'
Write-RecordingHtml $captures $htmlPath
Write-Host ('Saved {0} screens to {1}' -f $captures.Count, $htmlPath)
