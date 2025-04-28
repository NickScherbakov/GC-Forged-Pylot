Get-ChildItem -Recurse | ForEach-Object { 
    $indent = "  " * ($_.FullName.Split("\").Count - ($PWD.Path.Split("\").Count))
    $name = $_.Name
    if ($_.PSIsContainer) { $name = "[$name]" }
    "$indent$name" 
}