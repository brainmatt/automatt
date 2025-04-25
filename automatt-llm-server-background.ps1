
start powershell -windowstyle hidden {.\automatt-llm-server.ps1}
Start-Sleep -Seconds 2
$items = Get-WmiObject Win32_Process | Select ProcessId,CommandLine
foreach ($item in $items){
    $test=$item.CommandLine
 if ($test -like '*python*automatt-llm-server*') {
    $item.ProcessId
    $test
  }
}
