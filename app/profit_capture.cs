// Bounded selected-window capture. No OCR, scripts, network or child processes.
using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

internal static class ProfitCapture {
    [StructLayout(LayoutKind.Sequential)] private struct Rect { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] private static extern bool GetWindowRect(IntPtr handle, out Rect rect);
    [DllImport("user32.dll")] private static extern bool PrintWindow(IntPtr handle, IntPtr dc, uint flags);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] private static extern int GetWindowText(IntPtr handle, StringBuilder text, int count);
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr handle, out uint pid);
    [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr handle);
    [DllImport("user32.dll")] private static extern bool IsIconic(IntPtr handle);
    [DllImport("user32.dll")] private static extern bool SetProcessDpiAwarenessContext(IntPtr context);

    private static uint CheckWindow(IntPtr handle, string expectedTitle) {
        var text = new StringBuilder(513);
        uint pid;
        GetWindowText(handle, text, text.Capacity);
        GetWindowThreadProcessId(handle, out pid);
        if (pid == 0 || text.ToString() != expectedTitle || !IsWindowVisible(handle) || IsIconic(handle))
            throw new InvalidOperationException();
        using (var process = Process.GetProcessById(checked((int)pid))) {
            if (process.ProcessName.IndexOf("profit", StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidOperationException();
        }
        return pid;
    }

    private static int Main(string[] args) {
        string output = null;
        bool created = false;
        try {
            if (args.Length == 2 && args[0] == "--diagnostic-image") {
                output = args[1];
                if (!Path.IsPathRooted(output) || Path.GetExtension(output) != ".bmp") throw new ArgumentException();
                using (var image = new Bitmap(700, 100)) {
                    using (var graphics = Graphics.FromImage(image))
                    using (var font = new Font("Arial", 32, FontStyle.Regular, GraphicsUnit.Pixel)) {
                        graphics.Clear(Color.White);
                        graphics.DrawString("JEVE OCR 12345", font, Brushes.Black, 20, 25);
                    }
                    using (var stream = new FileStream(output, FileMode.CreateNew, FileAccess.Write, FileShare.None)) {
                        created = true;
                        image.Save(stream, ImageFormat.Bmp);
                    }
                }
                return 0;
            }
            if (args.Length != 7) throw new ArgumentException();
            long number = long.Parse(args[0], CultureInfo.InvariantCulture);
            string title = args[1];
            int x = int.Parse(args[2], CultureInfo.InvariantCulture), y = int.Parse(args[3], CultureInfo.InvariantCulture);
            int width = int.Parse(args[4], CultureInfo.InvariantCulture), height = int.Parse(args[5], CultureInfo.InvariantCulture);
            if (number <= 0 || title.Length > 512 || title.IndexOf("profit", StringComparison.OrdinalIgnoreCase) < 0 ||
                x < 0 || y < 0 || x > 10000 || y > 10000 || width < 32 || height < 32 || width > 4096 || height > 4096)
                throw new ArgumentException();
            output = args[6];
            if (!Path.IsPathRooted(output) || Path.GetExtension(output) != ".bmp") throw new ArgumentException();
            SetProcessDpiAwarenessContext(new IntPtr(-4)); // physical coordinates on Windows 10/11
            var handle = new IntPtr(number);
            uint pid = CheckWindow(handle, title);
            Rect rect;
            if (!GetWindowRect(handle, out rect)) throw new InvalidOperationException();
            int fullWidth = checked(rect.Right - rect.Left), fullHeight = checked(rect.Bottom - rect.Top);
            if (fullWidth <= 0 || fullHeight <= 0 || (long)fullWidth * fullHeight > 32000000 ||
                (long)x + width > fullWidth || (long)y + height > fullHeight) throw new ArgumentException();
            long capturedAt = (DateTime.UtcNow.Ticks - new DateTime(1970, 1, 1).Ticks) / TimeSpan.TicksPerMillisecond;
            using (var full = new Bitmap(fullWidth, fullHeight)) {
                using (var graphics = Graphics.FromImage(full)) {
                    var dc = graphics.GetHdc();
                    try { if (!PrintWindow(handle, dc, 2)) throw new InvalidOperationException(); }
                    finally { graphics.ReleaseHdc(dc); }
                }
                Rect after;
                if (CheckWindow(handle, title) != pid || !GetWindowRect(handle, out after) ||
                    after.Right - after.Left != fullWidth || after.Bottom - after.Top != fullHeight)
                    throw new InvalidOperationException();
                using (var crop = full.Clone(new Rectangle(x, y, width, height), PixelFormat.Format24bppRgb)) {
                    using (var stream = new FileStream(output, FileMode.CreateNew, FileAccess.Write, FileShare.None)) {
                        created = true;
                        crop.Save(stream, ImageFormat.Bmp);
                    }
                }
            }
            Console.WriteLine(capturedAt.ToString(CultureInfo.InvariantCulture));
            return 0;
        } catch {
            if (created) { try { File.Delete(output); } catch { } }
            Console.Error.WriteLine("Selected window capture unavailable");
            return 1;
        }
    }
}
