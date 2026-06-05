[Setup]
AppName=Layvix
AppVersion=3.4.5
DefaultDirName={autopf}\Layvix
DefaultGroupName=Layvix
OutputDir=installer
OutputBaseFilename=Layvix_Setup
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\Layvix.exe
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Run Layvix automatically when Windows starts"; GroupDescription: "Startup options"

[Files]
Source: "dist\Layvix\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs


[Icons]
Name: "{group}\Layvix"; Filename: "{app}\Layvix.exe"
Name: "{commondesktop}\Layvix"; Filename: "{app}\Layvix.exe"; Tasks: desktopicon
Name: "{userstartup}\Layvix"; Filename: "{app}\Layvix.exe"; Tasks: startup

[Run]
Filename: "{app}\Layvix.exe"; Description: "{cm:LaunchProgram,Layvix}"; Flags: nowait postinstall skipifsilent
