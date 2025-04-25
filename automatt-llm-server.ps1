
md -Force .\tasks > $null
rm tasks\task.json > $null
New-Item tasks\task.json -type file > $null
python automatt-llm-server.py
