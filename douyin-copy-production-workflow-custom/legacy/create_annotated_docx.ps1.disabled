param(
  [Parameter(Mandatory=$true)][string]$InputPath,
  [Parameter(Mandatory=$true)][string]$OutputDir
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Escape-XmlText([string]$s) {
  return [System.Security.SecurityElement]::Escape($s)
}

function Add-ZipEntry([System.IO.Compression.ZipArchive]$zip, [string]$name, [string]$content) {
  $entry = $zip.CreateEntry($name)
  $stream = $entry.Open()
  $writer = New-Object System.IO.StreamWriter($stream, [System.Text.UTF8Encoding]::new($false))
  $writer.Write($content)
  $writer.Close()
  $stream.Close()
}

function Add-TextRun([System.Text.StringBuilder]$builder, [string]$text, [bool]$highlight) {
  if ([string]::IsNullOrEmpty($text)) {
    return
  }
  $escaped = Escape-XmlText $text
  if ($highlight) {
    [void]$builder.Append("<w:r><w:rPr><w:highlight w:val=`"yellow`"/></w:rPr><w:t xml:space=`"preserve`">$escaped</w:t></w:r>")
  }
  else {
    [void]$builder.Append("<w:r><w:t xml:space=`"preserve`">$escaped</w:t></w:r>")
  }
}

function Convert-LineToParagraphXml([string]$line) {
  $builder = New-Object System.Text.StringBuilder
  [void]$builder.Append("<w:p>")
  $pos = 0
  $pattern = "\[\[RISKNOTE:(.*?)\]\]"
  $matches = [regex]::Matches($line, $pattern)
  foreach ($m in $matches) {
    if ($m.Index -gt $pos) {
      Add-TextRun $builder $line.Substring($pos, $m.Index - $pos) $false
    }
    Add-TextRun $builder $m.Groups[1].Value $true
    $pos = $m.Index + $m.Length
  }
  if ($pos -lt $line.Length) {
    Add-TextRun $builder $line.Substring($pos) $false
  }
  [void]$builder.Append("</w:p>")
  return $builder.ToString()
}

$text = Get-Content -LiteralPath $InputPath -Raw -Encoding UTF8

$riskItems = @(
  @{ Phrase = "拿捏人性"; Suggestion = "高风险表达，发布前重点审核上下文，可在口播解释为看懂机制，但原词此处保留" },
  @{ Phrase = "主导一切关系"; Suggestion = "攻击性较强，注意不要被理解为操控他人，原词此处保留" },
  @{ Phrase = "主导关系"; Suggestion = "平台可能判定为强控制倾向，建议剪辑时配合自我成长语境，原词此处保留" },
  @{ Phrase = "征服世界"; Suggestion = "强刺激词，适合保留气势，但注意不要连续堆叠，原词此处保留" },
  @{ Phrase = "征服"; Suggestion = "高压词，发布时留意上下文是否过度攻击，原词此处保留" },
  @{ Phrase = "最黑暗"; Suggestion = "强钩子词，可留，但不要与太多暴力化词连续出现" },
  @{ Phrase = "残酷丛林"; Suggestion = "丛林叙事风险中等，适合做世界观包装，避免延伸为现实伤害" },
  @{ Phrase = "冰冷残酷"; Suggestion = "情绪压迫感强，可保留，但建议搭配认知觉醒语境" },
  @{ Phrase = "残酷"; Suggestion = "高频压迫词，注意密度，原词此处保留" },
  @{ Phrase = "撕碎"; Suggestion = "暴力化隐喻，建议审核字幕呈现强度，原词此处保留" },
  @{ Phrase = "生吞"; Suggestion = "身体化强刺激词，可能增加审核风险，原词此处保留" },
  @{ Phrase = "操控"; Suggestion = "高风险词，若出现需重点审核，原词此处保留" },
  @{ Phrase = "主宰"; Suggestion = "强控制词，注意和自我主导区分，原词此处保留" }
) | Sort-Object { $_.Phrase.Length } -Descending

$annotated = $text
foreach ($item in $riskItems) {
  $phrase = [string]$item.Phrase
  $idx = $annotated.IndexOf($phrase, [System.StringComparison]::Ordinal)
  if ($idx -ge 0) {
    $insertAt = $idx + $phrase.Length
    $note = "[[RISKNOTE:（风险建议：$($item.Suggestion)）]]"
    $annotated = $annotated.Insert($insertAt, $note)
  }
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputPath = Join-Path $OutputDir "扩写稿-风险旁注版-$timestamp.docx"

$docxParas = New-Object System.Text.StringBuilder
foreach ($line in ($annotated -split "\r?\n")) {
  [void]$docxParas.Append((Convert-LineToParagraphXml $line))
}

$documentXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>扩写稿风险旁注版</w:t></w:r></w:p>
    <w:p><w:r><w:t>说明：正文原词未改写，仅在部分风险词首次出现处追加黄色高亮风险建议。</w:t></w:r></w:p>
    $($docxParas.ToString())
    <w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
  </w:body>
</w:document>
"@

$contentTypes = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"@

$rels = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"@

$wordRels = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"@

if (Test-Path -LiteralPath $outputPath) {
  Remove-Item -LiteralPath $outputPath -Force
}
$zip = [System.IO.Compression.ZipFile]::Open($outputPath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
  Add-ZipEntry $zip "[Content_Types].xml" $contentTypes
  Add-ZipEntry $zip "_rels/.rels" $rels
  Add-ZipEntry $zip "word/_rels/document.xml.rels" $wordRels
  Add-ZipEntry $zip "word/document.xml" $documentXml
}
finally {
  $zip.Dispose()
}

[pscustomobject]@{
  OutputPath = $outputPath
  OriginalChars = $text.Length
  AnnotatedChars = $annotated.Length
} | ConvertTo-Json -Compress
