\
# PowerShell script to create a desktop shortcut for the POS app
$WshShell = New-Object -ComObject WScript.Shell
$ShortcutPath = "$Env:UserProfile\Desktop\POS_App.lnk"
$TargetPath = "C:\sakatsu_pos\start_pos.bat"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = "C:\sakatsu_pos"
$Shortcut.IconLocation = "C:\Windows\System32\shell32.dll, 44"
$Shortcut.Save()
Write-Output "Shortcut created at $ShortcutPath"
