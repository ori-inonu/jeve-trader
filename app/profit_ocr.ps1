param([long]$Handle,[string]$ExpectedTitle,[int]$X,[int]$Y,[int]$Width,[int]$Height,[string]$ImagePath)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Drawing,System.Runtime.WindowsRuntime
Add-Type @'
using System;
using System.Drawing;
using System.Diagnostics;
using System.Text;
using System.Runtime.InteropServices;
public class ProfitPixels {
 [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left,Top,Right,Bottom; }
 [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out Rect r);
 [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s,int n);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h,out uint pid);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
 public static void Save(long handle,string expectedTitle,int x,int y,int width,int height,string path) {
  var h=new IntPtr(handle); var title=new StringBuilder(513); uint pid;
  GetWindowText(h,title,513); GetWindowThreadProcessId(h,out pid);
  if(title.ToString()!=expectedTitle || expectedTitle.IndexOf("profit",StringComparison.OrdinalIgnoreCase)<0 || !IsWindowVisible(h) || IsIconic(h)) throw new Exception("Janela mudou");
  using(var process=Process.GetProcessById((int)pid)) {
   if(process.ProcessName.IndexOf("profit",StringComparison.OrdinalIgnoreCase)<0) throw new Exception("Processo mudou");
  }
  Rect r; if(!GetWindowRect(h,out r)) throw new Exception("Janela indisponivel");
  if((long)(r.Right-r.Left)*(r.Bottom-r.Top)>32000000) throw new Exception("Janela fora do limite de captura");
  if(x<0 || y<0 || x+width>r.Right-r.Left || y+height>r.Bottom-r.Top) throw new Exception("Regiao fora da janela");
  using(var full=new Bitmap(r.Right-r.Left,r.Bottom-r.Top)) {
   using(var g=Graphics.FromImage(full)) { var dc=g.GetHdc(); try { if(!PrintWindow(new IntPtr(handle),dc,2)) throw new Exception("Pixels indisponiveis"); } finally { g.ReleaseHdc(dc); } }
   using(var crop=full.Clone(new Rectangle(x,y,width,height),System.Drawing.Imaging.PixelFormat.Format32bppArgb)) crop.Save(path,System.Drawing.Imaging.ImageFormat.Png);
  }
 }
}
'@
function Await-WinRT($Operation,[Type]$ResultType) {
 $method = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
 $task = $method.MakeGenericMethod($ResultType).Invoke($null,@($Operation))
 $task.Wait(); $task.Result
}
try {
 $capturedAt=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
 [ProfitPixels]::Save($Handle,$ExpectedTitle,$X,$Y,$Width,$Height,$ImagePath)
 $fileType=[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
 $streamType=[Windows.Storage.Streams.IRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]
 $decoderType=[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
 $bitmapType=[Windows.Graphics.Imaging.SoftwareBitmap,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
 $ocrType=[Windows.Media.Ocr.OcrEngine,Windows.Media.Ocr,ContentType=WindowsRuntime]
 $resultType=[Windows.Media.Ocr.OcrResult,Windows.Media.Ocr,ContentType=WindowsRuntime]
 $file=Await-WinRT ($fileType::GetFileFromPathAsync($ImagePath)) $fileType
 $stream=Await-WinRT ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) $streamType
 $decoder=Await-WinRT ($decoderType::CreateAsync($stream)) $decoderType
 $bitmap=Await-WinRT ($decoder.GetSoftwareBitmapAsync()) $bitmapType
 $engine=$ocrType::TryCreateFromUserProfileLanguages()
 if(!$engine) { throw 'Idioma OCR Windows não instalado' }
 $result=Await-WinRT ($engine.RecognizeAsync($bitmap)) $resultType
 @{lines=@($result.Lines | ForEach-Object {$_.Text});captured_at_ms=$capturedAt} | ConvertTo-Json -Compress
} finally {
 if($bitmap) {$bitmap.Dispose()}; if($stream) {$stream.Dispose()}
 if(Test-Path -LiteralPath $ImagePath) { Remove-Item -LiteralPath $ImagePath -Force }
}
