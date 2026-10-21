# Script chạy tự động 3 phiên cào, mỗi phiên cách nhau 3 tiếng
# Hiển thị trực tiếp log trên cửa sổ PowerShell này để theo dõi

$Host.UI.RawUI.WindowTitle = "UIT Confession Crawler - Live Auto Runner"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONPATH = "src"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   TIEN TRINH TU DONG CAO 3 PHIEN UIT CONFESSION (3 TIENG/LAN)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

for ($i = 1; $i -le 3; $i++) {
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "`n>>> [PHAT LENH PHIEN $i / 3] - Bat dau luc: $now <<<" -ForegroundColor Green
    
    # 1. Chay crawl
    python -m uitconf.cli discover --warmup
    
    # 2. Rebuild clean data
    Write-Host "`n[TỰ ĐỘNG] Dang xu ly chuan hoa va an danh du lieu..." -ForegroundColor Yellow
    python -m uitconf.cli build
    
    # 3. Cap nhat review_labeled.csv & gold.csv
    Write-Host "[TỰ ĐỘNG] Dang dong bo nhan va xuat review_labeled.csv..." -ForegroundColor Yellow
    python scripts/auto_label.py
    
    Write-Host "[THANH CONG] Hoan tat phien $i / 3!" -ForegroundColor Green
    
    if ($i -lt 3) {
        Write-Host "`nDang nghi 3 tieng (10800 giay) truoc khi bat dau phien tiep theo de bao ve tai khoan..." -ForegroundColor Magenta
        Write-Host "Cua so nay se giu nguyen va dem nguoc. Ban co the yen tam treo may!" -ForegroundColor Gray
        
        # Dem nguoc 3 tieng (10800 giay), in thong bao moi 30 phut
        for ($sec = 10800; $sec -gt 0; $sec -= 1800) {
            Start-Sleep -Seconds 1800
            $rem = ($sec - 1800) / 3600
            $t = Get-Date -Format "HH:mm:ss"
            Write-Host "[$t] Con $rem tieng nua den phien $($i+1)..." -ForegroundColor DarkGray
        }
    }
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "   DA HOAN TAT TOAN BO 3 PHIEN CAO THEO KE HOACH!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Read-Host -Prompt "Nhan Enter de dong cua so..."
