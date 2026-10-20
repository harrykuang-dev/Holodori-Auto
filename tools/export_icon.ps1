# Export the approved artwork as transparent Windows application icon assets.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$projectRoot = Split-Path -Parent $PSScriptRoot
$assetDirectory = Join-Path $projectRoot 'assets'
$artwork = [Drawing.Image]::FromFile((Join-Path $assetDirectory 'holodori-artwork.png'))
$canvas = [Drawing.Bitmap]::new(512,512,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [Drawing.Graphics]::FromImage($canvas)
$graphics.Clear([Drawing.Color]::Transparent)
$graphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$graphics.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::HighQuality
# Standard icon padding and a clean rounded silhouette around the approved tile.
$edge = 12
$extent = 512 - 2 * $edge
$diameter = 192
$outline = [Drawing.Drawing2D.GraphicsPath]::new()
$outline.AddArc($edge,$edge,$diameter,$diameter,180,90)
$outline.AddArc(512-$edge-$diameter,$edge,$diameter,$diameter,270,90)
$outline.AddArc(512-$edge-$diameter,512-$edge-$diameter,$diameter,$diameter,0,90)
$outline.AddArc($edge,512-$edge-$diameter,$diameter,$diameter,90,90)
$outline.CloseFigure()
$mask = [Drawing.Bitmap]::new(512,512,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
$maskGraphics = [Drawing.Graphics]::FromImage($mask)
$maskGraphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
$maskGraphics.FillPath([Drawing.Brushes]::White,$outline)
$maskGraphics.Dispose()
$inset = [int][Math]::Round($artwork.Width * 0.06)
$sourceRectangle = [Drawing.Rectangle]::new($inset,$inset,$artwork.Width-2*$inset,$artwork.Height-2*$inset)
$graphics.DrawImage($artwork,[Drawing.Rectangle]::new($edge,$edge,$extent,$extent),$sourceRectangle,[Drawing.GraphicsUnit]::Pixel)
$graphics.Dispose()
for ($y=0; $y -lt 512; $y++) {
    for ($x=0; $x -lt 512; $x++) {
        $pixel = $canvas.GetPixel($x,$y)
        $alpha = $mask.GetPixel($x,$y).A
        $color = if ($alpha -eq 0) { [Drawing.Color]::FromArgb(0,0,0,0) }
                 else { [Drawing.Color]::FromArgb($alpha,$pixel.R,$pixel.G,$pixel.B) }
        $canvas.SetPixel($x,$y,$color)
    }
}
$canvas.Save((Join-Path $assetDirectory 'holodori.png'),[Drawing.Imaging.ImageFormat]::Png)
$sizes = @(16,20,24,32,40,48,64,128,256)
$entries = @()
foreach ($size in $sizes) {
    $bitmap = [Drawing.Bitmap]::new($size,$size,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [Drawing.Graphics]::FromImage($bitmap)
    $g.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.DrawImage($canvas,[Drawing.Rectangle]::new(0,0,$size,$size))
    $g.Dispose()
    $stream = [IO.MemoryStream]::new()
    $bitmap.Save($stream,[Drawing.Imaging.ImageFormat]::Png)
    $entries += ,@{ Size=$size; Bytes=$stream.ToArray() }
    $stream.Dispose(); $bitmap.Dispose()
}
$file = [IO.File]::Create((Join-Path $assetDirectory 'holodori.ico'))
$writer = [IO.BinaryWriter]::new($file)
$writer.Write([uint16]0); $writer.Write([uint16]1); $writer.Write([uint16]$entries.Count)
$offset = 6 + 16 * $entries.Count
foreach ($entry in $entries) {
    $dimension = if ($entry.Size -eq 256) { 0 } else { $entry.Size }
    $writer.Write([byte]$dimension); $writer.Write([byte]$dimension)
    $writer.Write([byte]0); $writer.Write([byte]0)
    $writer.Write([uint16]1); $writer.Write([uint16]32)
    $writer.Write([uint32]$entry.Bytes.Length); $writer.Write([uint32]$offset)
    $offset += $entry.Bytes.Length
}
foreach ($entry in $entries) { $writer.Write([byte[]]$entry.Bytes) }
$writer.Dispose(); $file.Dispose()
$outline.Dispose(); $mask.Dispose(); $canvas.Dispose(); $artwork.Dispose()
Write-Output "Exported assets/holodori.png and assets/holodori.ico ($($sizes -join ', ') px)."
