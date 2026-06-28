param(
  [Parameter(Mandatory = $true)]
  [string]$Path,

  [string]$OutCsv = "",

  [double]$FingerprintSimilarityThreshold = 0.45
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.Web

$LabelMechanism = (-join @([char]0x6587,[char]0x6848,[char]0x6838,[char]0x5FC3,[char]0x673A,[char]0x5236,[char]0xFF1A))
$LabelMechanismClean = "mechanism" + [char]0xFF1A
$LabelFingerprint = (-join @([char]0x6587,[char]0x6848,[char]0x6307,[char]0x7EB9,[char]0xFF1A))
$LabelTitlePrefix = (-join @([char]0x6807,[char]0x9898))
$FullVersion = (-join @([char]0x5B8C,[char]0x6574,[char]0x672A,[char]0x5220,[char]0x51CF,[char]0x7248))
$FingerprintFields = @(
  "source_id",
  "raw_title_digest",
  "opening_hook",
  "body_claim",
  "scene_anchor",
  "case_or_example",
  "target_subject",
  "audience_state",
  "desire_vector",
  "fear_vector",
  "core_conflict",
  "mistaken_belief",
  "behavior_signal",
  "behavior_chain",
  "relationship_mechanism",
  "emotional_trigger",
  "power_shift",
  "novelty_point",
  "non_reusable_anchor",
  "anti_copy_terms",
  "unique_term_seed",
  "forbidden_generic_terms",
  "result_promise",
  "fingerprint_key",
  "fingerprint_granularity_score",
  "specificity_diagnosis"
)
$P0FingerprintFields = @(
  "source_id",
  "body_claim",
  "scene_anchor",
  "behavior_signal",
  "behavior_chain",
  "emotional_trigger",
  "power_shift",
  "non_reusable_anchor",
  "fingerprint_key"
)
$GenericTerms = @(
  (-join @([char]0x4FE1,[char]0x606F,[char]0x5BC6,[char]0x5EA6)),
  (-join @([char]0x6CE8,[char]0x610F,[char]0x529B)),
  (-join @([char]0x5956,[char]0x8D4F,[char]0x56DE,[char]0x8DEF)),
  (-join @([char]0x60C5,[char]0x7EEA,[char]0x8FFD,[char]0x9010)),
  (-join @([char]0x4F4E,[char]0x9700,[char]0x6C42,[char]0x611F)),
  (-join @([char]0x7A00,[char]0x7F3A,[char]0x611F)),
  (-join @([char]0x4E0A,[char]0x5934)),
  (-join @([char]0x5E95,[char]0x5C42,[char]0x903B,[char]0x8F91)),
  (-join @([char]0x5438,[char]0x5F15,[char]0x529B))
)

function Normalize-Text([string]$Value) {
  if ($null -eq $Value) { return "" }
  return ([regex]::Replace($Value, '[^\p{L}\p{N}]', '')).Trim()
}

function Get-CharNgrams([string]$Value, [int]$Size = 2) {
  $key = Normalize-Text $Value
  $grams = New-Object System.Collections.Generic.List[string]
  if (-not $key) { return @() }
  if ($key.Length -le $Size) { return @($key) }
  for ($i = 0; $i -le $key.Length - $Size; $i++) {
    $grams.Add($key.Substring($i, $Size))
  }
  return @($grams)
}

function Get-JaccardSimilarity([string]$A, [string]$B) {
  $aSet = @{}
  $bSet = @{}
  foreach ($gram in (Get-CharNgrams $A 2)) { $aSet[$gram] = $true }
  foreach ($gram in (Get-CharNgrams $B 2)) { $bSet[$gram] = $true }
  if ($aSet.Count -eq 0 -and $bSet.Count -eq 0) { return 1.0 }
  if ($aSet.Count -eq 0 -or $bSet.Count -eq 0) { return 0.0 }

  $intersection = 0
  $union = @{}
  foreach ($key in $aSet.Keys) {
    $union[$key] = $true
    if ($bSet.ContainsKey($key)) { $intersection++ }
  }
  foreach ($key in $bSet.Keys) { $union[$key] = $true }
  return [double]$intersection / [double]$union.Count
}

function Get-AnchorTokens([object]$Record) {
  $tokens = New-Object System.Collections.Generic.List[string]
  foreach ($value in @($Record.OpeningHook, $Record.SceneAnchor, $Record.BehaviorSignal, $Record.UniqueTermSeed, $Record.BodyClaim, $Record.BehaviorChain, $Record.NonReusableAnchor)) {
    if (-not $value) { continue }
    foreach ($part in ([regex]::Split($value, '[,，/|、;\s]+'))) {
      $token = Normalize-Text $part
      if ($token.Length -ge 2) { $tokens.Add($token) }
    }
  }
  return @($tokens | Select-Object -Unique)
}

function Test-TitleHasFingerprintAnchor([object]$Record) {
  $titleKey = Normalize-Text $Record.Title1
  if (-not $titleKey) { return $true }
  $tokens = Get-AnchorTokens $Record
  if ($tokens.Count -eq 0) { return $true }
  foreach ($token in $tokens) {
    if ($titleKey.Contains($token) -or $token.Contains($titleKey)) {
      return $true
    }
    if ((Get-JaccardSimilarity $titleKey $token) -ge 0.22) {
      return $true
    }
  }
  return $false
}

function Get-RowValue($Row, [string[]]$Names) {
  foreach ($name in $Names) {
    if ($Row.PSObject.Properties.Name -contains $name) {
      return [string]$Row.$name
    }
  }
  return ""
}

function Get-FingerprintScore([hashtable]$Fingerprint) {
  $score = 0
  foreach ($field in $FingerprintFields) {
    if ($Fingerprint.ContainsKey($field) -and $Fingerprint[$field].Trim().Length -gt 0) {
      $score++
    }
  }
  return $score
}

function Get-GranularityScore([hashtable]$Fingerprint, [string]$Title1) {
  $score = 0
  $missingP0 = @()

  foreach ($field in $P0FingerprintFields) {
    if ($Fingerprint.ContainsKey($field) -and $Fingerprint[$field].Trim().Length -gt 0) {
      $score += 1
    } else {
      $missingP0 += $field
    }
  }

  $detailFields = @("opening_hook", "scene_anchor", "case_or_example", "behavior_signal", "behavior_chain", "non_reusable_anchor")
  $detailCount = 0
  foreach ($field in $detailFields) {
    if ($Fingerprint.ContainsKey($field) -and (Normalize-Text $Fingerprint[$field]).Length -ge 4) {
      $detailCount++
    }
  }
  if ($detailCount -ge 3) { $score += 2 } elseif ($detailCount -ge 2) { $score += 1 }

  if ($Fingerprint["behavior_chain"] -and ([regex]::Split($Fingerprint["behavior_chain"], '->|→|>').Count -ge 3)) { $score += 1 }
  if ($Fingerprint["power_shift"] -and (Normalize-Text $Fingerprint["power_shift"]).Length -ge 6) { $score += 1 }
  if ($Fingerprint["unique_term_seed"] -and (([regex]::Split($Fingerprint["unique_term_seed"], '[,，/|、;\s]+') | Where-Object { (Normalize-Text $_).Length -ge 2 }).Count -ge 2)) { $score += 1 }
  if ($Fingerprint["fingerprint_key"] -and (Normalize-Text $Fingerprint["fingerprint_key"]).Length -ge 18) { $score += 1 }

  $anchorRecord = [pscustomobject]@{
    Title1 = $Title1
    OpeningHook = $Fingerprint["opening_hook"]
    SceneAnchor = $Fingerprint["scene_anchor"]
    BehaviorSignal = $Fingerprint["behavior_signal"]
    UniqueTermSeed = $Fingerprint["unique_term_seed"]
    BodyClaim = $Fingerprint["body_claim"]
    BehaviorChain = $Fingerprint["behavior_chain"]
    NonReusableAnchor = $Fingerprint["non_reusable_anchor"]
  }
  if (Test-TitleHasFingerprintAnchor $anchorRecord) { $score += 1 }

  return [pscustomobject]@{
    Score = [Math]::Min(10, $score)
    MissingP0 = ($missingP0 -join ",")
  }
}

function Test-OnlyGenericFingerprint([string]$FingerprintKey) {
  $key = Normalize-Text $FingerprintKey
  if (-not $key) { return $false }

  $generic = ""
  foreach ($term in $GenericTerms) {
    $generic += (Normalize-Text $term)
  }

  $remaining = $key
  foreach ($term in $GenericTerms) {
    $termKey = Normalize-Text $term
    if ($termKey) {
      $remaining = $remaining.Replace($termKey, "")
    }
  }

  return ($remaining.Length -le 4 -and $key.Length -gt 0 -and $generic.Length -gt 0)
}

function New-EmptyFingerprint() {
  $fingerprint = @{}
  foreach ($field in $FingerprintFields) {
    $fingerprint[$field] = ""
  }
  return $fingerprint
}

function Get-DocxLines([string]$FilePath) {
  $fs = [System.IO.File]::Open($FilePath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
  try {
    $zip = [System.IO.Compression.ZipArchive]::new($fs, [System.IO.Compression.ZipArchiveMode]::Read)
    try {
      $entry = $zip.GetEntry("word/document.xml")
      if ($null -eq $entry) { return @() }
      $stream = $entry.Open()
      try {
        $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8)
        $xmlText = $reader.ReadToEnd()
      } finally {
        if ($reader) { $reader.Close() }
        $stream.Close()
      }
    } finally {
      $zip.Dispose()
    }
  } finally {
    $fs.Dispose()
  }

  $lines = @()
  try {
    [xml]$xml = $xmlText
    $ns = [System.Xml.XmlNamespaceManager]::new($xml.NameTable)
    $ns.AddNamespace("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main")
    foreach ($p in $xml.SelectNodes("//w:p", $ns)) {
      $parts = @()
      foreach ($t in $p.SelectNodes(".//w:t", $ns)) { $parts += $t.InnerText }
      $line = ($parts -join "").Trim()
      if ($line.Length -gt 0) { $lines += $line }
    }
  } catch {
    $matches = [regex]::Matches($xmlText, '<w:t[^>]*>(.*?)</w:t>', 'Singleline')
    $buffer = New-Object System.Collections.Generic.List[string]
    foreach ($m in $matches) {
      $text = [System.Web.HttpUtility]::HtmlDecode($m.Groups[1].Value)
      if ($text.Trim().Length -gt 0) { $buffer.Add($text) }
    }
    $lines = @($buffer)
  }
  return $lines
}

function Extract-TitleRecordFromLines([string]$FileName, [string[]]$Lines) {
  $mechanism = ""
  $title1 = ""
  $title1Second = ""
  $concepts = New-Object System.Collections.Generic.List[string]
  $fingerprint = New-EmptyFingerprint

  for ($i = 0; $i -lt $Lines.Count; $i++) {
    $line = $Lines[$i].Trim()
    if (-not $mechanism -and $line.StartsWith($LabelMechanism)) {
      $mechanism = $line.Substring($LabelMechanism.Length).Trim()
    }
    if (-not $mechanism -and $line.StartsWith($LabelMechanismClean)) {
      $mechanism = $line.Substring($LabelMechanismClean.Length).Trim()
    }
    if ($line -eq ($LabelTitlePrefix + "1" + [char]0xFF1A) -and $i + 1 -lt $Lines.Count) {
      $title1 = $Lines[$i + 1].Trim()
      if ($i + 2 -lt $Lines.Count) { $title1Second = $Lines[$i + 2].Trim() }
    }
    if ($line.StartsWith($LabelTitlePrefix) -and $line.EndsWith([string][char]0xFF1A) -and $i + 1 -lt $Lines.Count) {
      $concepts.Add($Lines[$i + 1].Trim())
    }
    foreach ($field in $FingerprintFields) {
      $prefix = $field + [char]0xFF1A
      if ($line.StartsWith($prefix)) {
        $fingerprint[$field] = $line.Substring($prefix.Length).Trim()
      }
    }
  }

  $fingerprintScore = Get-FingerprintScore $fingerprint
  $granularity = Get-GranularityScore $fingerprint $title1

  return [pscustomobject]@{
    File = $FileName
    FingerprintKey = $fingerprint["fingerprint_key"]
    FingerprintKeyNorm = Normalize-Text $fingerprint["fingerprint_key"]
    FingerprintScore = $fingerprintScore
    FingerprintGranularityScore = $granularity.Score
    MissingP0 = $granularity.MissingP0
    OpeningHook = $fingerprint["opening_hook"]
    SceneAnchor = $fingerprint["scene_anchor"]
    BehaviorSignal = $fingerprint["behavior_signal"]
    BodyClaim = $fingerprint["body_claim"]
    BehaviorChain = $fingerprint["behavior_chain"]
    NonReusableAnchor = $fingerprint["non_reusable_anchor"]
    UniqueTermSeed = $fingerprint["unique_term_seed"]
    Mechanism = $mechanism
    Title1 = $title1
    Title1Second = $title1Second
    Title1Pair = (($title1 + " " + $title1Second).Trim())
    MechanismKey = Normalize-Text $mechanism
    Title1Key = Normalize-Text $title1
    Title1PairKey = Normalize-Text (($title1 + $title1Second).Trim())
    FirstLineConcepts = ($concepts -join " | ")
  }
}

$records = @()
if (Test-Path -LiteralPath $Path -PathType Leaf) {
  if ([System.IO.Path]::GetExtension($Path).ToLowerInvariant() -eq ".csv") {
    $csvRows = Import-Csv -LiteralPath $Path
    foreach ($r in $csvRows) {
      $mechanism = Get-RowValue $r @("Mechanism", "mechanism")
      $title1 = Get-RowValue $r @("Title1", "title1", "Title", "title")
      $file = Get-RowValue $r @("File", "file", "Source", "source", "source_id")
      $fingerprint = New-EmptyFingerprint
      foreach ($field in $FingerprintFields) {
        $fingerprint[$field] = Get-RowValue $r @($field, ($field.Substring(0,1).ToUpperInvariant() + $field.Substring(1)))
      }
      if (-not $fingerprint["fingerprint_key"]) {
        $fingerprint["fingerprint_key"] = Get-RowValue $r @("FingerprintKey", "Fingerprint", "fingerprint")
      }
      $fingerprintScore = Get-FingerprintScore $fingerprint
      $granularity = Get-GranularityScore $fingerprint $title1
      $records += [pscustomobject]@{
        File = $file
        FingerprintKey = $fingerprint["fingerprint_key"]
        FingerprintKeyNorm = Normalize-Text $fingerprint["fingerprint_key"]
        FingerprintScore = $fingerprintScore
        FingerprintGranularityScore = $granularity.Score
        MissingP0 = $granularity.MissingP0
        OpeningHook = $fingerprint["opening_hook"]
        SceneAnchor = $fingerprint["scene_anchor"]
        BehaviorSignal = $fingerprint["behavior_signal"]
        BodyClaim = $fingerprint["body_claim"]
        BehaviorChain = $fingerprint["behavior_chain"]
        NonReusableAnchor = $fingerprint["non_reusable_anchor"]
        UniqueTermSeed = $fingerprint["unique_term_seed"]
        Mechanism = $mechanism
        Title1 = $title1
        Title1Second = ""
        Title1Pair = $title1
        MechanismKey = Normalize-Text $mechanism
        Title1Key = Normalize-Text $title1
        Title1PairKey = Normalize-Text $title1
        FirstLineConcepts = ""
      }
    }
  } else {
    throw "Path is a file but not a CSV: $Path"
  }
} else {
  Get-ChildItem -LiteralPath $Path -File -Filter "*.docx" |
    Where-Object { -not $_.Name.StartsWith('~$') } |
    Sort-Object Name |
    ForEach-Object {
      $lines = Get-DocxLines $_.FullName
      $records += Extract-TitleRecordFromLines $_.Name $lines
    }
}

$issues = New-Object System.Collections.Generic.List[object]
foreach ($field in @("MechanismKey", "Title1Key", "Title1PairKey")) {
  $groups = $records |
    Where-Object { $_.$field -and $_.$field.Length -gt 0 } |
    Group-Object $field |
    Where-Object { $_.Count -gt 1 }

  foreach ($g in $groups) {
    foreach ($item in $g.Group) {
      $issues.Add([pscustomobject]@{
        Type = $field
        Key = $g.Name
        Count = $g.Count
        File = $item.File
        Mechanism = $item.Mechanism
        Title1 = $item.Title1
        Title1Pair = $item.Title1Pair
      })
    }
  }
}

$fingerprintGroups = $records |
  Where-Object { $_.FingerprintKeyNorm -and $_.FingerprintKeyNorm.Length -gt 0 } |
  Group-Object FingerprintKeyNorm |
  Where-Object { $_.Count -gt 1 }

foreach ($g in $fingerprintGroups) {
  foreach ($item in $g.Group) {
    $issues.Add([pscustomobject]@{
      Type = "FingerprintKey"
      Key = $g.Name
      Count = $g.Count
      File = $item.File
      Mechanism = $item.Mechanism
      Title1 = $item.Title1
      Title1Pair = $item.Title1Pair
    })
  }
}

for ($i = 0; $i -lt $records.Count; $i++) {
  for ($j = $i + 1; $j -lt $records.Count; $j++) {
    $left = $records[$i]
    $right = $records[$j]
    if (-not $left.FingerprintKeyNorm -or -not $right.FingerprintKeyNorm) { continue }
    if ($left.FingerprintKeyNorm -eq $right.FingerprintKeyNorm) { continue }
    if ($left.FingerprintKeyNorm.Length -lt 12 -or $right.FingerprintKeyNorm.Length -lt 12) { continue }

    $similarity = Get-JaccardSimilarity $left.FingerprintKeyNorm $right.FingerprintKeyNorm
    if ($similarity -ge $FingerprintSimilarityThreshold) {
      foreach ($item in @($left, $right)) {
        $issues.Add([pscustomobject]@{
          Type = "SimilarFingerprintKey"
          Key = ("score={0:N2}; {1} <-> {2}" -f $similarity, $left.File, $right.File)
          Count = 2
          File = $item.File
          Mechanism = $item.Mechanism
          Title1 = $item.Title1
          Title1Pair = $item.Title1Pair
        })
      }
    }
  }
}

foreach ($record in $records) {
  if (-not $record.FingerprintKeyNorm) {
    $issues.Add([pscustomobject]@{
      Type = "MissingFingerprintKey"
      Key = ""
      Count = 1
      File = $record.File
      Mechanism = $record.Mechanism
      Title1 = $record.Title1
      Title1Pair = $record.Title1Pair
    })
  } elseif ($record.FingerprintKeyNorm.Length -lt 12) {
    $issues.Add([pscustomobject]@{
      Type = "WeakFingerprintKey"
      Key = $record.FingerprintKey
      Count = 1
      File = $record.File
      Mechanism = $record.Mechanism
      Title1 = $record.Title1
      Title1Pair = $record.Title1Pair
    })
  } elseif (Test-OnlyGenericFingerprint $record.FingerprintKey) {
    $issues.Add([pscustomobject]@{
      Type = "GenericFingerprintKey"
      Key = $record.FingerprintKey
      Count = 1
      File = $record.File
      Mechanism = $record.Mechanism
      Title1 = $record.Title1
      Title1Pair = $record.Title1Pair
    })
  }

  if ($record.FingerprintScore -ge 8 -and -not (Test-TitleHasFingerprintAnchor $record)) {
    $issues.Add([pscustomobject]@{
      Type = "Title1NoFingerprintAnchor"
      Key = $record.FingerprintKey
      Count = 1
      File = $record.File
      Mechanism = $record.Mechanism
      Title1 = $record.Title1
      Title1Pair = $record.Title1Pair
    })
  }

  if ($record.FingerprintScore -gt 0 -and $record.FingerprintScore -lt 5) {
    $issues.Add([pscustomobject]@{
      Type = "ThinFingerprint"
      Key = "score=$($record.FingerprintScore)"
      Count = 1
      File = $record.File
      Mechanism = $record.Mechanism
      Title1 = $record.Title1
      Title1Pair = $record.Title1Pair
    })
  }

  if ($record.MissingP0) {
    $issues.Add([pscustomobject]@{
      Type = "MissingP0FingerprintFields"
      Key = $record.MissingP0
      Count = 1
      File = $record.File
      Mechanism = $record.Mechanism
      Title1 = $record.Title1
      Title1Pair = $record.Title1Pair
    })
  }

  if ($record.FingerprintGranularityScore -gt 0 -and $record.FingerprintGranularityScore -lt 8) {
    $issues.Add([pscustomobject]@{
      Type = "LowFingerprintGranularity"
      Key = "score=$($record.FingerprintGranularityScore)"
      Count = 1
      File = $record.File
      Mechanism = $record.Mechanism
      Title1 = $record.Title1
      Title1Pair = $record.Title1Pair
    })
  }
}

Write-Host "Total: $($records.Count)"
Write-Host "Duplicate groups: $(($issues | Group-Object Type,Key).Count)"
Write-Host "Duplicate issue rows: $($issues.Count)"

if ($issues.Count -gt 0) {
  $issues | Sort-Object Type,Key,File | Format-Table -AutoSize
} else {
  Write-Host "No duplicate mechanisms/title1/title1-pairs/fingerprints found."
}

if ($OutCsv) {
  $issues | Export-Csv -LiteralPath $OutCsv -NoTypeInformation -Encoding UTF8
  Write-Host "Wrote duplicate report: $OutCsv"
}
