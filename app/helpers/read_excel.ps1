# Read only an already-open Excel range. Never create Excel, open/save a file,
# recalculate, change protection/security, execute formulas or submit orders.
param([Parameter(Mandatory=$true)][string]$ConfigBase64)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$excel = $null
$book = $null
$sheet = $null
$range = $null
$books = $null
$worksheets = $null
$errorCode = 'INVALID_CONFIG'
try {
    $json = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($ConfigBase64))
    $config = $json | ConvertFrom-Json
    if (-not $config.workbook -or -not $config.sheet -or
        $config.cell_range -notmatch '^\$?[A-Za-z]{1,3}\$?[1-9][0-9]*:\$?[A-Za-z]{1,3}\$?[1-9][0-9]*$') {
        throw 'Invalid configuration'
    }
    # Independently bound the range before requesting Value2, even if this
    # helper is invoked outside the Python validator.
    [void]($config.cell_range -match '^\$?([A-Za-z]{1,3})\$?([1-9][0-9]*):\$?([A-Za-z]{1,3})\$?([1-9][0-9]*)$')
    $startColumn = 0
    foreach ($character in $Matches[1].ToUpper().ToCharArray()) {
        $startColumn = $startColumn * 26 + [int]$character - 64
    }
    $endColumn = 0
    foreach ($character in $Matches[3].ToUpper().ToCharArray()) {
        $endColumn = $endColumn * 26 + [int]$character - 64
    }
    $startRow = [long]$Matches[2]
    $endRow = [long]$Matches[4]
    $width = $endColumn - $startColumn + 1
    $height = $endRow - $startRow + 1
    if ($width -lt 1 -or $width -gt 64 -or $height -lt 2 -or $height -gt 5001 -or
        $endColumn -gt 16384 -or $endRow -gt 1048576) { throw 'Invalid range bounds' }
    $errorCode = 'EXCEL_NOT_RUNNING'
    $excel = [Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application')
    $errorCode = 'WORKBOOK_NOT_FOUND'
    $books = $excel.Workbooks
    for ($i = 1; $i -le $books.Count; $i++) {
        $candidate = $books.Item($i)
        if ($candidate.Name -ieq [string]$config.workbook -or $candidate.FullName -ieq [string]$config.workbook) {
            $book = $candidate
            break
        }
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($candidate)
    }
    if ($null -eq $book) { throw 'Workbook not found' }
    $errorCode = 'SHEET_NOT_FOUND'
    $worksheets = $book.Worksheets
    $sheet = $worksheets.Item([string]$config.sheet)
    $errorCode = 'READ_FAILED'
    $range = $sheet.Range([string]$config.cell_range)
    $values = $range.Value2
    $rows = New-Object 'System.Collections.Generic.List[object]'
    if ($values -is [Array] -and $values.Rank -eq 2) {
        if ($values.GetLength(0) -gt 5001 -or $values.GetLength(1) -gt 64) {
            throw 'Range too large'
        }
        for ($r = $values.GetLowerBound(0); $r -le $values.GetUpperBound(0); $r++) {
            $row = New-Object 'System.Collections.Generic.List[object]'
            for ($c = $values.GetLowerBound(1); $c -le $values.GetUpperBound(1); $c++) {
                $row.Add($values.GetValue($r, $c))
            }
            $rows.Add($row.ToArray())
        }
    } else { throw 'Expected rectangular range' }
    @{ ok=$true; rows=$rows.ToArray() } | ConvertTo-Json -Depth 6 -Compress
} catch {
    # Deliberately do not expose paths, COM exception details or workbook data.
    @{ ok=$false; error=$errorCode } | ConvertTo-Json -Compress
} finally {
    foreach ($object in @($range, $sheet, $worksheets, $book, $books, $excel)) {
        if ($null -ne $object -and [Runtime.InteropServices.Marshal]::IsComObject($object)) {
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($object)
        }
    }
    # Do not call Excel.Quit(): Excel belongs to the user.
}
