PS C:\Users\Администратор> Get-WmiObject Win32_Processor


Caption           : Intel64 Family 6 Model 167 Stepping 1
DeviceID          : CPU0
Manufacturer      : GenuineIntel
MaxClockSpeed     : 3504
Name              : 11th Gen Intel(R) Core(TM) i9-11900KF @ 3.50GHz
SocketDesignation : U3E1

PS C:\Users\Администратор> Get-WmiObject Win32_VideoController


__GENUS                      : 2
__CLASS                      : Win32_VideoController
__SUPERCLASS                 : CIM_PCVideoController
__DYNASTY                    : CIM_ManagedSystemElement
__RELPATH                    : Win32_VideoController.DeviceID="VideoController1"
__PROPERTY_COUNT             : 59
__DERIVATION                 : {CIM_PCVideoController, CIM_VideoController, CIM_Controller, CIM_LogicalDevice...}
__SERVER                     : WS2022-04
__NAMESPACE                  : root\cimv2
__PATH                       : \\WS2022-04\root\cimv2:Win32_VideoController.DeviceID="VideoController1"
AcceleratorCapabilities      :
AdapterCompatibility         : Advanced Micro Devices, Inc.
AdapterDACType               : Internal DAC(400MHz)
AdapterRAM                   : 4293918720
Availability                 : 3
CapabilityDescriptions       :
Caption                      : AMD Radeon RX 580 2048SP
ColorTableEntries            :
ConfigManagerErrorCode       : 0
ConfigManagerUserConfig      : False
CreationClassName            : Win32_VideoController
CurrentBitsPerPixel          : 32
CurrentHorizontalResolution  : 1920
CurrentNumberOfColors        : 4294967296
CurrentNumberOfColumns       : 0
CurrentNumberOfRows          : 0
CurrentRefreshRate           : 75
CurrentScanMode              : 4
CurrentVerticalResolution    : 1080
Description                  : AMD Radeon RX 580 2048SP
DeviceID                     : VideoController1
DeviceSpecificPens           :
DitherType                   : 0
DriverDate                   : 20221025000000.000000-000
DriverVersion                : 31.0.12044.3
ErrorCleared                 :
ErrorDescription             :
ICMIntent                    :
ICMMethod                    :
InfFilename                  : oem45.inf
InfSection                   : ati2mtag_Polaris10
InstallDate                  :
InstalledDisplayDrivers      : C:\WINDOWS\System32\DriverStore\FileRepository\u0385558.inf_amd64_a02c8b890e9f278a\B3854
                               77\aticfx64.dll,C:\WINDOWS\System32\DriverStore\FileRepository\u0385558.inf_amd64_a02c8b
                               890e9f278a\B385477\aticfx64.dll,C:\WINDOWS\System32\DriverStore\FileRepository\u0385558.
                               inf_amd64_a02c8b890e9f278a\B385477\aticfx64.dll,C:\WINDOWS\System32\DriverStore\FileRepo
                               sitory\u0385558.inf_amd64_a02c8b890e9f278a\B385477\amdxc64.dll
LastErrorCode                :
MaxMemorySupported           :
MaxNumberControlled          :
MaxRefreshRate               : 75
MinRefreshRate               : 50
Monochrome                   : False
Name                         : AMD Radeon RX 580 2048SP
NumberOfColorPlanes          :
NumberOfVideoPages           :
PNPDeviceID                  : PCI\VEN_1002&DEV_6FDF&SUBSYS_0B311002&REV_EF\4&B36F5C3&0&0008
PowerManagementCapabilities  :
PowerManagementSupported     :
ProtocolSupported            :
ReservedSystemPaletteEntries :
SpecificationVersion         :
Status                       : OK
StatusInfo                   :
SystemCreationClassName      : Win32_ComputerSystem
SystemName                   : WS2022-04
SystemPaletteEntries         :
TimeOfLastReset              :
VideoArchitecture            : 5
VideoMemoryType              : 2
VideoMode                    :
VideoModeDescription         : Цвета: 1920 x 1080 x 4294967296
VideoProcessor               : AMD Radeon Graphics Processor (0x6FDF)
PSComputerName               : WS2022-04


Не вижу, но VRAM 8Gb

PS C:\Users\Администратор> Get-WmiObject Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum


Count    : 4
Average  :
Sum      : 51539607552
Maximum  :
Minimum  :
Property : Capacity
