
 param (
    [string]$run = ""
    [string]$list = ""
    [string]$provider = "google",
    [string]$model = "gemini-2.0-flash"
    [string]$baseurl = ""
 )

python automatt-cli.py -run -model $model -provider $provider -baseurl $baseurl 2>null


