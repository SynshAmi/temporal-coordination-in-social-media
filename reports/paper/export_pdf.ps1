param([string]$Docx, [string]$Pdf)
# Exports the final Word document to PDF with Microsoft Word's own exporter.
# Word's COM interface needs absolute paths; relative paths are resolved here.
$Docx = (Resolve-Path -LiteralPath $Docx).Path
$Pdf = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Pdf))
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
  $d = $w.Documents.Open($Docx, $false, $true)
  "pages: " + $d.ComputeStatistics(2)
  $d.ExportAsFixedFormat($Pdf, 17)   # wdExportFormatPDF
  $d.Close(0)
} finally { $w.Quit() }
