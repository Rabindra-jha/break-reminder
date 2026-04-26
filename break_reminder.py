"""
Break Reminder - Desktop Background App
======================================
Runs silently in system tray, pops a beautiful WPF alert every 20 minutes.
Build to .exe:  python -m PyInstaller --onefile --windowed --name "BreakReminder" break_reminder.py

Requirements:
    pip install pystray pillow
"""

import threading
import subprocess
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import time
import sys

# ─────────────────────────────────────────────
#  CONFIG  (tweak these as needed)
# ─────────────────────────────────────────────
INTERVAL_MINUTES = 20
APP_NAME         = "Break Reminder"
ALERT_TITLE      = "👀 Time for a Break!"
ALERT_MESSAGE    = (
    "You've been working for 20 minutes.\n\n"
    "✅  Look away from the screen (20-20-20 rule)\n"
    "🚶  Stand up and stretch\n"
    "💧  Drink some water\n\n"
    "Click OK when you're ready to continue."
)


# ─────────────────────────────────────────────
#  TRAY ICON  (generated programmatically)
# ─────────────────────────────────────────────
def create_tray_icon() -> Image.Image:
    """Draw a simple green circle icon for the system tray."""
    size = 64
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Outer circle
    draw.ellipse([4, 4, size - 4, size - 4], fill="#27ae60", outline="#1e8449", width=3)
    # Clock hands (simple cross to suggest a timer)
    cx, cy = size // 2, size // 2
    draw.line([cx, cy - 16, cx, cy], fill="white", width=4)   # 12 o'clock hand
    draw.line([cx, cy, cx + 12, cy], fill="white", width=3)   # 3 o'clock hand
    return img


# ─────────────────────────────────────────────
#  ALERT DIALOG  (custom WPF via PowerShell)
# ─────────────────────────────────────────────
def show_alert():
    """
    Spawns a fully custom WPF window via PowerShell.
    1100x1100, dark theme, large fonts, animated gradient background.
    Completely isolated process — no tkinter/thread conflicts.
    """
    ps_script = r"""
Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase

[xml]$xaml = @"
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Break Reminder"
    Width="1100" Height="1100"
    MinWidth="1100" MinHeight="1100"
    WindowStartupLocation="CenterScreen"
    Topmost="True"
    ResizeMode="NoResize"
    WindowStyle="None"
    AllowsTransparency="True"
    Background="Transparent">

  <Window.Resources>
    <!-- OK Button hover style -->
    <Style x:Key="OkButtonStyle" TargetType="Button">
      <Setter Property="Background" Value="#27AE60"/>
      <Setter Property="Foreground" Value="White"/>
      <Setter Property="FontSize" Value="28"/>
      <Setter Property="FontWeight" Value="Bold"/>
      <Setter Property="FontFamily" Value="Segoe UI"/>
      <Setter Property="Width" Value="320"/>
      <Setter Property="Height" Value="80"/>
      <Setter Property="Cursor" Value="Hand"/>
      <Setter Property="BorderThickness" Value="0"/>
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="Button">
            <Grid>
              <!-- Glow ring: slightly larger than button so blur radiates outward only -->
              <Border x:Name="glow" CornerRadius="44" BorderThickness="0"
                      Background="#2ECC71" Margin="-6" Opacity="0">
                <Border.Effect>
                  <DropShadowEffect Color="#2ECC71" BlurRadius="20" ShadowDepth="0" Opacity="0.9"/>
                </Border.Effect>
              </Border>
              <!-- Solid background — no effect, covers glow interior entirely -->
              <Border x:Name="border" Background="{TemplateBinding Background}"
                      CornerRadius="40" BorderThickness="0"/>
              <!-- Text always on top, never inside an effected element -->
              <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
            </Grid>
            <ControlTemplate.Triggers>
              <Trigger Property="IsMouseOver" Value="True">
                <Setter TargetName="border" Property="Background" Value="#2ECC71"/>
                <Setter TargetName="glow"   Property="Opacity"    Value="1"/>
              </Trigger>
              <Trigger Property="IsPressed" Value="True">
                <Setter TargetName="border" Property="Background" Value="#1E8449"/>
                <Setter TargetName="glow"   Property="Opacity"    Value="0"/>
              </Trigger>
            </ControlTemplate.Triggers>
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>
  </Window.Resources>

  <!-- Outer rounded card -->
  <Border CornerRadius="32" Margin="60">
    <Border.Background>
      <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
        <GradientStop Color="#0D1B2A" Offset="0"/>
        <GradientStop Color="#1B2838" Offset="0.5"/>
        <GradientStop Color="#0A1628" Offset="1"/>
      </LinearGradientBrush>
    </Border.Background>
    <Border.Effect>
      <DropShadowEffect Color="Black" BlurRadius="30" ShadowDepth="0" Opacity="0.8"/>
    </Border.Effect>

    <Grid ClipToBounds="True">
      <Grid.RowDefinitions>
        <RowDefinition Height="*"/>
        <RowDefinition Height="Auto"/>
      </Grid.RowDefinitions>

      <!-- Decorative top glow circle -->
      <Ellipse Width="600" Height="600"
               HorizontalAlignment="Center" VerticalAlignment="Top"
               Margin="0,-250,0,0" Opacity="0.07">
        <Ellipse.Fill>
          <RadialGradientBrush>
            <GradientStop Color="#27AE60" Offset="0"/>
            <GradientStop Color="Transparent" Offset="1"/>
          </RadialGradientBrush>
        </Ellipse.Fill>
      </Ellipse>

      <!-- Main content -->
      <StackPanel Grid.Row="0" VerticalAlignment="Center" HorizontalAlignment="Center"
                  Margin="80,60,80,40">

        <!-- Big eye / break icon -->
        <Border Width="160" Height="160" CornerRadius="80" HorizontalAlignment="Center"
                Margin="0,0,0,48">
          <Border.Background>
            <RadialGradientBrush>
              <GradientStop Color="#27AE60" Offset="0"/>
              <GradientStop Color="#1E8449" Offset="1"/>
            </RadialGradientBrush>
          </Border.Background>
          <Border.Effect>
            <DropShadowEffect Color="#27AE60" BlurRadius="50" ShadowDepth="0" Opacity="0.6"/>
          </Border.Effect>
          <TextBlock Text="&#x23F0;" FontSize="80"
                     HorizontalAlignment="Center" VerticalAlignment="Center"
                     Margin="0,8,0,0"/>
        </Border>

        <!-- Title -->
        <TextBlock Text="Time for a Break!"
                   FontSize="64" FontWeight="Black"
                   FontFamily="Segoe UI"
                   Foreground="White"
                   HorizontalAlignment="Center"
                   TextAlignment="Center"
                   Margin="0,0,0,16">
          <TextBlock.Effect>
            <DropShadowEffect Color="#27AE60" BlurRadius="20" ShadowDepth="0" Opacity="0.5"/>
          </TextBlock.Effect>
        </TextBlock>

        <!-- Subtitle -->
        <TextBlock Text="You've been working for 20 minutes"
                   FontSize="28" FontWeight="Normal"
                   FontFamily="Segoe UI"
                   Foreground="#8899AA"
                   HorizontalAlignment="Center"
                   TextAlignment="Center"
                   Margin="0,0,0,64"/>

        <!-- Tip cards row -->
        <StackPanel Orientation="Horizontal" HorizontalAlignment="Center"
                    Margin="0,0,0,64">

          <!-- Card 1 -->
          <Border Width="220" Height="200" CornerRadius="24" Margin="16,0">
            <Border.Background>
              <SolidColorBrush Color="#1A2A3A"/>
            </Border.Background>
            <Border.BorderBrush>
              <SolidColorBrush Color="#27AE60" Opacity="0.3"/>
            </Border.BorderBrush>
            <Border.BorderThickness>1.5</Border.BorderThickness>
            <StackPanel VerticalAlignment="Center" HorizontalAlignment="Center">
              <Image x:Name="EyeGif" Width="72" Height="72"
                     HorizontalAlignment="Center" Margin="0,0,0,16"
                     RenderOptions.BitmapScalingMode="HighQuality"/>
              <TextBlock Text="20-20-20 Rule" FontSize="22" FontWeight="SemiBold"
                         Foreground="White" HorizontalAlignment="Center"
                         TextAlignment="Center"/>
              <TextBlock Text="Look 20ft away&#x0a;for 20 seconds" FontSize="18"
                         Foreground="#8899AA" HorizontalAlignment="Center"
                         TextAlignment="Center" Margin="0,8,0,0"/>
            </StackPanel>
          </Border>

          <!-- Card 2 -->
          <Border Width="220" Height="200" CornerRadius="24" Margin="16,0">
            <Border.Background>
              <SolidColorBrush Color="#1A2A3A"/>
            </Border.Background>
            <Border.BorderBrush>
              <SolidColorBrush Color="#3498DB" Opacity="0.3"/>
            </Border.BorderBrush>
            <Border.BorderThickness>1.5</Border.BorderThickness>
            <StackPanel VerticalAlignment="Center" HorizontalAlignment="Center">
              <Image x:Name="StretchGif" Width="72" Height="72"
                     HorizontalAlignment="Center" Margin="0,0,0,16"
                     RenderOptions.BitmapScalingMode="HighQuality"/>
              <TextBlock Text="Stretch" FontSize="22" FontWeight="SemiBold"
                         Foreground="White" HorizontalAlignment="Center"/>
              <TextBlock Text="Stand up and&#x0a;move around" FontSize="18"
                         Foreground="#8899AA" HorizontalAlignment="Center"
                         TextAlignment="Center" Margin="0,8,0,0"/>
            </StackPanel>
          </Border>

          <!-- Card 3 -->
          <Border Width="220" Height="200" CornerRadius="24" Margin="16,0">
            <Border.Background>
              <SolidColorBrush Color="#1A2A3A"/>
            </Border.Background>
            <Border.BorderBrush>
              <SolidColorBrush Color="#2980B9" Opacity="0.3"/>
            </Border.BorderBrush>
            <Border.BorderThickness>1.5</Border.BorderThickness>
            <StackPanel VerticalAlignment="Center" HorizontalAlignment="Center">
              <Image x:Name="WaterGif" Width="72" Height="72"
                     HorizontalAlignment="Center" Margin="0,0,0,16"
                     RenderOptions.BitmapScalingMode="HighQuality"/>
              <TextBlock Text="Hydrate" FontSize="22" FontWeight="SemiBold"
                         Foreground="White" HorizontalAlignment="Center"/>
              <TextBlock Text="Drink a glass&#x0a;of water" FontSize="18"
                         Foreground="#8899AA" HorizontalAlignment="Center"
                         TextAlignment="Center" Margin="0,8,0,0"/>
            </StackPanel>
          </Border>

        </StackPanel>

      </StackPanel>

      <!-- OK Button -->
      <StackPanel Grid.Row="1" HorizontalAlignment="Center" Margin="0,0,0,72">
        <Button x:Name="OkButton" Content="I'm taking a break  ✓"
                Style="{StaticResource OkButtonStyle}"/>
        <TextBlock Text="Next reminder in 20 minutes"
                   FontSize="20" Foreground="#55667A"
                   HorizontalAlignment="Center" Margin="0,20,0,0"
                   FontFamily="Segoe UI"/>
      </StackPanel>

    </Grid>
  </Border>
</Window>
"@

$reader = [System.Xml.XmlNodeReader]::new($xaml)
$window = [Windows.Markup.XamlReader]::Load($reader)

# Scale a BitmapFrame down to fit within 100x100 to save memory
$scaleFrame = {
    param($frame)
    $maxPx = 100
    if ($frame.PixelWidth -le $maxPx -and $frame.PixelHeight -le $maxPx) {
        $frame.Freeze(); return $frame
    }
    $scale = [Math]::Min($maxPx / $frame.PixelWidth, $maxPx / $frame.PixelHeight)
    $tb = [System.Windows.Media.Imaging.TransformedBitmap]::new(
        $frame, [System.Windows.Media.ScaleTransform]::new($scale, $scale)
    )
    $tb.Freeze(); return $tb
}

$loadGif = {
    param($path)
    $stream = [System.IO.File]::OpenRead($path)
    $dec = [System.Windows.Media.Imaging.GifBitmapDecoder]::new(
        $stream,
        [System.Windows.Media.Imaging.BitmapCreateOptions]::None,
        [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad
    )
    $stream.Close()
    return @($dec.Frames | ForEach-Object { & $scaleFrame $_ })
}

# ── Water (Hydrate) ──────────────────────────────────────────
$script:waterFrames = & $loadGif "C:\Users\rabin\Desktop\files\water.gif"
$script:waterIndex  = 10
$waterImage         = $window.FindName("WaterGif")
$waterImage.Source  = $script:waterFrames[10]

$waterTimer          = [System.Windows.Threading.DispatcherTimer]::new()
$waterTimer.Interval = [TimeSpan]::FromMilliseconds(80)
$waterTimer.Add_Tick({
    $script:waterIndex++
    if ($script:waterIndex -gt 120) { $script:waterIndex = 10 }
    $waterImage.Source = $script:waterFrames[$script:waterIndex]
})
$waterTimer.Start()

# ── Stretch ──────────────────────────────────────────────────
$script:stretchFrames = & $loadGif "C:\Users\rabin\Desktop\files\stretching.gif"
$script:stretchIndex  = 5
$stretchImage         = $window.FindName("StretchGif")
$stretchImage.Source  = $script:stretchFrames[5]

$stretchTimer          = [System.Windows.Threading.DispatcherTimer]::new()
$stretchTimer.Interval = [TimeSpan]::FromMilliseconds(80)
$stretchTimer.Add_Tick({
    $script:stretchIndex++
    if ($script:stretchIndex -ge $script:stretchFrames.Count) { $script:stretchIndex = 5 }
    $stretchImage.Source = $script:stretchFrames[$script:stretchIndex]
})
$stretchTimer.Start()

# ── Eye (20-20-20) ───────────────────────────────────────────
$script:eyeFrames = & $loadGif "C:\Users\rabin\Desktop\files\eye.gif"
$script:eyeIndex  = 5
$eyeImage         = $window.FindName("EyeGif")
$eyeImage.Source  = $script:eyeFrames[5]

$eyeTimer          = [System.Windows.Threading.DispatcherTimer]::new()
$eyeTimer.Interval = [TimeSpan]::FromMilliseconds(80)
$eyeTimer.Add_Tick({
    $script:eyeIndex++
    if ($script:eyeIndex -ge $script:eyeFrames.Count) { $script:eyeIndex = 5 }
    $eyeImage.Source = $script:eyeFrames[$script:eyeIndex]
})
$eyeTimer.Start()

$window.Add_Closed({ $waterTimer.Stop(); $stretchTimer.Stop(); $eyeTimer.Stop() })

# ── Force true transparency ──────────────────────────────
# Add-Type -AssemblyName System.Windows.Shell
# $chrome = [System.Windows.Shell.WindowChrome]::new()
# $chrome.ResizeBorderThickness = [System.Windows.Thickness]::new(0)
# $chrome.CaptionHeight         = 0
# $chrome.CornerRadius          = [System.Windows.CornerRadius]::new(0)
# $chrome.GlassFrameThickness   = [System.Windows.Thickness]::new(-1)
# [System.Windows.Shell.WindowChrome]::SetWindowChrome($window, $chrome)
# $window.Background            = [System.Windows.Media.Brushes]::Transparent
# ────────────────────────────────────────────────────────
$window.WindowStyle        = [System.Windows.WindowStyle]::None
$window.AllowsTransparency = $true
# $window.Background         = [System.Windows.Media.Brushes]::Transparent
$window.Background = [System.Windows.Media.Brushes]::Transparent
$okButton = $window.FindName("OkButton")
$okButton.Add_Click({ $window.Close() })


$window.Add_KeyDown({
    param($s, $e)
    if ($e.Key -eq 'Return' -or $e.Key -eq 'Escape') { $window.Close() }
})

$window.ShowDialog() | Out-Null

"""

    subprocess.run(
        ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
        shell=False,
        creationflags=subprocess.CREATE_NO_WINDOW
    )


# ─────────────────────────────────────────────
#  TIMER LOOP  (background thread)
# ─────────────────────────────────────────────
class BreakTimer:
    def __init__(self):
        self._stop_event  = threading.Event()
        self._alert_event = threading.Event()   # signals main thread to show alert
        self._thread      = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            # Wait INTERVAL_MINUTES or until stopped
            self._stop_event.wait(timeout=INTERVAL_MINUTES * 60)
            if not self._stop_event.is_set():
                self._alert_event.set()   # wake main thread

    def consume_alert(self) -> bool:
        """Returns True if an alert is pending (and clears it)."""
        if self._alert_event.is_set():
            self._alert_event.clear()
            return True
        return False


# ─────────────────────────────────────────────
#  TRAY APPLICATION
# ─────────────────────────────────────────────
class BreakReminderApp:
    def __init__(self):
        self.timer = BreakTimer()
        self.icon  = None

    # ── Tray menu callbacks ──────────────────
    def on_quit(self, icon, item):
        self.timer.stop()
        icon.stop()

    def on_show_now(self, icon, item):
        """Manual 'Show Alert Now' from tray menu."""
        show_alert()

    # ── Build & run tray icon ────────────────
    def run(self):
        self.timer.start()

        menu = pystray.Menu(
            item("⏰  " + APP_NAME, lambda i, it: None, enabled=False),  # label
            pystray.Menu.SEPARATOR,
            item("Show Alert Now",  self.on_show_now),
            item("Quit",            self.on_quit),
        )

        self.icon = pystray.Icon(
            name    = APP_NAME,
            icon    = create_tray_icon(),
            title   = APP_NAME,
            menu    = menu,
        )

        # Poll for pending alerts inside pystray's own thread
        # by using a lightweight periodic check on a separate thread
        threading.Thread(target=self._alert_poller, daemon=True).start()

        self.icon.run()

    # ── Alert poller ─────────────────────────
    def _alert_poller(self):
        """
        Checks every second if the timer fired.
        When it has, shows the dialog on the main OS thread
        via icon.notify (safe cross-thread call).
        """
        while True:
            time.sleep(1)
            if self.timer.consume_alert():
                # pystray's notify is thread-safe; use it as a bridge
                # to trigger the real Tkinter dialog via a lambda hook
                self._trigger_alert_on_main_thread()

    def _trigger_alert_on_main_thread(self):
        """
        pystray does not expose a run_on_main_thread helper on all platforms,
        so we spawn a minimal thread that itself calls Tkinter.
        Tkinter dialog is safe here because it creates its own Tk() root.
        """
        t = threading.Thread(target=show_alert, daemon=True)
        t.start()
        t.join()   # wait for user to click OK before resuming timer


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    # Prevent multiple instances (Windows-only guard)
    if sys.platform == "win32":
        import ctypes
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, APP_NAME)
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            sys.exit(0)

    app = BreakReminderApp()
    app.run()


if __name__ == "__main__":
    main()