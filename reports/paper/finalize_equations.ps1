param([string]$Docx)
# Replaces [[EQn]] placeholders with native Word equations built from
# UnicodeMath linear format; "#(n)" gives Word's right-aligned equation number.
# Word's COM interface needs an absolute path; relative paths are resolved here.
$Docx = (Resolve-Path -LiteralPath $Docx).Path
$FA  = [char]0x2061   # function application (upright "ln")
$SUM = [char]0x2211   # n-ary summation
$BOX = [char]0x2592   # n-ary operand separator
$LB  = [char]0x3016; $RB = [char]0x3017   # invisible grouping brackets
$MIN = [char]0x2212   # minus sign
$BAR = [char]0x0305   # combining overline (x-bar)
$SQ  = [char]0x221A   # square root
$EM  = [char]0x2003   # em space
$Q   = '"'            # quoted text renders upright
$IN  = [char]0x2208   # element of
$BIN = [char]0x00A6   # binomial separator: (n¦k)
$EXP = [char]::ConvertFromUtf32(0x1D53C)   # double-struck E (expectation)

# (1) Gini coefficient of a sorted non-negative vector
# (2) density of a K-edge sample is determined by its endpoint count N_K
# (3) expected distinct endpoints under uniform K-of-m edge sampling without replacement
$eqs = @{
  1 = "G(x)=(2$SUM" + "_(i=1)^n$BOX$LB" + "i x_((i))$RB$MIN(n+1)$SUM" + "_(i=1)^n$BOX" + "x_((i)))/(n$SUM" + "_(i=1)^n$BOX" + "x_((i)))#(1)"
  2 = "D_K=K/(N_K (N_K$MIN" + "1))#(2)"
  3 = "$EXP[N_K]=$SUM" + "_(v$IN" + "V)$BOX$LB[1$MIN$LB($LB" + "m$MIN" + "d_v$RB$BIN" + "K)$RB/$LB(m$BIN" + "K)$RB]$RB#(3)"
}

$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
  $d = $w.Documents.Open($Docx)
  foreach ($n in 1..3) {
    $r = $d.Content
    $f = $r.Find
    $f.ClearFormatting()
    if (-not $f.Execute("[[EQ$n]]")) { throw "placeholder EQ$n not found" }
    $r.Text = $eqs[$n]
    $m = $d.OMaths.Add($r)
    $om = $m.OMaths.Item(1)
    $om.Type = 0          # wdOMathDisplay
    $om.BuildUp()
    "EQ$n built: " + $om.Range.Text.Length + " chars"
  }
  "equations in document: " + $d.OMaths.Count
  $d.Save()
  $d.Close()
} finally { $w.Quit() }
