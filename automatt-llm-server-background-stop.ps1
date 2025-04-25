$items = Get-WmiObject Win32_Process | Select ProcessId,CommandLine
foreach ($item in $items){
$test=$item.CommandLine 
 if ($test -like '*python*automatt-llm-server*') {
    $item.ProcessId
    $test
   Stop-Process -Id $item.ProcessId
  }
 
}
