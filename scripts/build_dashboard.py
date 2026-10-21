import json
import os
import pandas as pd

# Load data
df_gold = pd.read_csv('data/labeled/gold.csv')
conn_posts_count = 1434
conn_time_min = "23/08/2026"
conn_time_max = "06/10/2026"

# Load samples
with open('data/dashboard_samples.json', 'r', encoding='utf-8') as f:
    samples = json.load(f)

html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UIT Confession – Data & Sentiment Analytics Dashboard</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    :root {{
      --background: #0f172a;
      --card: #1e293b;
      --border: #334155;
      --foreground: #f8fafc;
      --muted: #94a3b8;
      --primary: #3b82f6;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --purple: #8b5cf6;
    }}
    body {{
      background-color: var(--background);
      color: var(--foreground);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }}
    .metric-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 0.75rem;
      padding: 1.25rem;
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .metric-card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }}
    .badge {{
      display: inline-block;
      padding: 0.25rem 0.6rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
    }}
    .badge-khong-lien-quan {{ background: #475569; color: #f8fafc; }}
    .badge-trung-tinh {{ background: #1e40af; color: #93c5fd; }}
    .badge-hoi-dap {{ background: #b45309; color: #fde68a; }}
    .badge-tich-cuc {{ background: #065f46; color: #a7f3d0; }}
    .badge-tieu-cuc {{ background: #991b1b; color: #fecaca; }}
    .badge-aspect {{ background: #3730a3; color: #c7d2fe; }}
    .progress-bar {{
      height: 0.75rem;
      border-radius: 9999px;
      overflow: hidden;
      background: #334155;
      display: flex;
    }}
  </style>
</head>
<body class="p-4 md:p-8 antialiased">
  <div class="max-w-7xl mx-auto space-y-6">

    <!-- Top Header -->
    <header class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[var(--border)]">
      <div>
        <div class="flex items-center gap-3">
          <span class="text-2xl">🎓</span>
          <h1 class="text-2xl md:text-3xl font-bold tracking-tight">UIT Confession Sentiment & Aspect Dashboard</h1>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
            Crawler Active
          </span>
        </div>
        <p class="text-sm text-[var(--muted)] mt-1">Hệ thống phân tích thái độ sinh viên & khía cạnh đào tạo (Selenium + ABSA)</p>
      </div>
      <div class="flex items-center gap-3 text-xs text-[var(--muted)]">
        <span class="bg-[var(--card)] px-3 py-2 rounded-lg border border-[var(--border)]">
          📅 Phạm vi: <strong class="text-[var(--foreground)]">{conn_time_min} → {conn_time_max}</strong>
        </span>
        <button onclick="window.location.reload()" class="bg-blue-600 hover:bg-blue-500 text-white font-medium px-3 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
          Làm mới
        </button>
      </div>
    </header>

    <!-- KPI Grid -->
    <section class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="metric-card">
        <div class="text-xs uppercase font-semibold text-[var(--muted)] tracking-wider">Tổng bài viết đã cào</div>
        <div class="text-3xl font-extrabold text-blue-400 mt-2">1,434</div>
        <div class="text-xs text-emerald-400 mt-1 flex items-center gap-1">
          ↑ +51 bài phiên gần nhất
        </div>
      </div>
      <div class="metric-card">
        <div class="text-xs uppercase font-semibold text-[var(--muted)] tracking-wider">Đơn vị phân tích (Clean Units)</div>
        <div class="text-3xl font-extrabold text-indigo-400 mt-2">1,308</div>
        <div class="text-xs text-[var(--muted)] mt-1">Đã khử nhiễu & ẩn danh 2 lớp</div>
      </div>
      <div class="metric-card">
        <div class="text-xs uppercase font-semibold text-[var(--muted)] tracking-wider">Liên quan trường học (UIT)</div>
        <div class="text-3xl font-extrabold text-amber-400 mt-2">429 <span class="text-sm font-normal text-[var(--muted)]">(32.8%)</span></div>
        <div class="text-xs text-[var(--muted)] mt-1">Được chuyển tiếp sang ABSA</div>
      </div>
      <div class="metric-card">
        <div class="text-xs uppercase font-semibold text-[var(--muted)] tracking-wider">Không liên quan (Tạp âm)</div>
        <div class="text-3xl font-extrabold text-slate-400 mt-2">879 <span class="text-sm font-normal text-[var(--muted)]">(67.2%)</span></div>
        <div class="text-xs text-[var(--muted)] mt-1">Rao vặt, tìm đồ, tán gẫu</div>
      </div>
    </section>

    <!-- Charts Row 1 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Chart 1: Sentiment Distribution -->
      <div class="metric-card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-semibold flex items-center gap-2">
            <span>🎭</span> Phân bố Nhãn Cảm xúc & Phân loại (Gold Labels)
          </h2>
          <span class="text-xs text-[var(--muted)]">Tổng 1,308 mẫu</span>
        </div>

        <!-- Progress bar representation -->
        <div class="progress-bar my-3">
          <div style="width: 65.6%; background: #64748b;" title="Không liên quan: 65.6%"></div>
          <div style="width: 30.7%; background: #3b82f6;" title="Trung tính: 30.7%"></div>
          <div style="width: 3.4%; background: #f59e0b;" title="Hỏi đáp: 3.4%"></div>
          <div style="width: 0.38%; background: #10b981;" title="Tích cực: 0.38%"></div>
        </div>

        <div class="space-y-3 mt-4">
          <div class="flex items-center justify-between text-sm p-2 rounded-lg bg-slate-800/40 border border-slate-700/50">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-slate-500"></span>
              <span class="font-medium">Không liên quan (khong_lien_quan)</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="font-bold text-slate-300">858</span>
              <span class="text-xs text-[var(--muted)] w-12 text-right">65.60%</span>
            </div>
          </div>

          <div class="flex items-center justify-between text-sm p-2 rounded-lg bg-slate-800/40 border border-slate-700/50">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-blue-500"></span>
              <span class="font-medium">Trung tính (trung_tinh)</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="font-bold text-blue-400">401</span>
              <span class="text-xs text-[var(--muted)] w-12 text-right">30.66%</span>
            </div>
          </div>

          <div class="flex items-center justify-between text-sm p-2 rounded-lg bg-slate-800/40 border border-slate-700/50">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-amber-500"></span>
              <span class="font-medium">Hỏi đáp / Quy chế (hoi_dap)</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="font-bold text-amber-400">44</span>
              <span class="text-xs text-[var(--muted)] w-12 text-right">3.36%</span>
            </div>
          </div>

          <div class="flex items-center justify-between text-sm p-2 rounded-lg bg-slate-800/40 border border-slate-700/50">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
              <span class="font-medium">Tích cực (tich_cuc)</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="font-bold text-emerald-400">5</span>
              <span class="text-xs text-[var(--muted)] w-12 text-right">0.38%</span>
            </div>
          </div>
        </div>

        <div class="mt-4 p-3 rounded-lg bg-blue-950/30 border border-blue-900/50 text-xs text-blue-300">
          💡 <strong>Nhận định:</strong> Nhãn <em>tich_cuc</em> và <em>tieu_cuc</em> rất ít trong bài đăng confession gốc do sinh viên chủ yếu post để hỏi bài hoặc chia sẻ khách quan. Cảm xúc khen/chê mạnh sẽ bộc lộ nhiều hơn khi cào phần bình luận (comments).
        </div>
      </div>

      <!-- Chart 2: Aspect Distribution -->
      <div class="metric-card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-semibold flex items-center gap-2">
            <span>🏛️</span> 7 Khía cạnh Học đường Cốt lõi (Aspects)
          </h2>
          <span class="text-xs text-[var(--muted)]">Guideline v4.1 (Đã bỏ KTX)</span>
        </div>

        <div class="space-y-3">
          <!-- Item 1 -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium text-slate-200">1. Chương trình đào tạo (chuong_trinh)</span>
              <span class="font-bold text-indigo-400">146 bài (23.1%)</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-2.5">
              <div class="bg-indigo-500 h-2.5 rounded-full" style="width: 100%"></div>
            </div>
          </div>

          <!-- Item 2 -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium text-slate-200">2. Thi cử & Điểm số (thi_cu)</span>
              <span class="font-bold text-indigo-400">139 bài (22.0%)</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-2.5">
              <div class="bg-indigo-500 h-2.5 rounded-full" style="width: 95.2%"></div>
            </div>
          </div>

          <!-- Item 3 -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium text-slate-200">3. Giảng viên (giang_vien)</span>
              <span class="font-bold text-indigo-400">137 bài (21.6%)</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-2.5">
              <div class="bg-indigo-500 h-2.5 rounded-full" style="width: 93.8%"></div>
            </div>
          </div>

          <!-- Item 4 -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium text-slate-200">4. Thủ tục hành chính / DAA (hanh_chinh)</span>
              <span class="font-bold text-slate-300">62 bài (9.8%)</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-2.5">
              <div class="bg-blue-500 h-2.5 rounded-full" style="width: 42.5%"></div>
            </div>
          </div>

          <!-- Item 5 -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium text-slate-200">5. Đoàn - Hội & Hoạt động (doan_hoi)</span>
              <span class="font-bold text-slate-300">59 bài (9.3%)</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-2.5">
              <div class="bg-blue-500 h-2.5 rounded-full" style="width: 40.4%"></div>
            </div>
          </div>

          <!-- Item 6 -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium text-slate-200">6. Cơ sở vật chất / Wifi (co_so_vat_chat)</span>
              <span class="font-bold text-slate-300">52 bài (8.2%)</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-2.5">
              <div class="bg-teal-500 h-2.5 rounded-full" style="width: 35.6%"></div>
            </div>
          </div>

          <!-- Item 7 -->
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium text-slate-200">7. Học phí & Học bổng (hoc_phi)</span>
              <span class="font-bold text-slate-300">38 bài (6.0%)</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-2.5">
              <div class="bg-teal-500 h-2.5 rounded-full" style="width: 26.0%"></div>
            </div>
          </div>
        </div>

        <div class="mt-4 p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 text-xs text-slate-400">
          📌 <strong>Top 3 chủ đề nóng:</strong> Chiếm tới <strong>66.7%</strong> toàn bộ các thảo luận có khía cạnh tại UIT.
        </div>
      </div>

    </div>

    <!-- Charts Row 2: Timeline & Cross Matrix -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Timeline Chart -->
      <div class="metric-card lg:col-span-1">
        <h2 class="text-base font-semibold flex items-center gap-2 mb-4">
          <span>📈</span> Tiến độ Cào theo Tháng (2026)
        </h2>
        <div class="space-y-4">
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium">Tháng 09/2026 (Hoàn tất)</span>
              <span class="font-bold text-blue-400">899 bài (62.7%)</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-3">
              <div class="bg-blue-500 h-3 rounded-full" style="width: 100%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium">Tháng 08/2026 (Đang cào tiếp)</span>
              <span class="font-bold text-indigo-400">421 bài (29.4%)</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-3">
              <div class="bg-indigo-500 h-3 rounded-full" style="width: 46.8%"></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium">Tháng 10/2026 (Đầu tháng)</span>
              <span class="font-bold text-slate-400">114 bài (7.9%)</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-3">
              <div class="bg-slate-500 h-3 rounded-full" style="width: 12.7%"></div>
            </div>
          </div>
        </div>
        <div class="mt-6 p-3 rounded-lg bg-emerald-950/30 border border-emerald-900/50 text-xs text-emerald-300">
          🎯 <strong>Mục tiêu:</strong> Crawler đang tiếp tục đào sâu qua tháng 8 để hướng tới mốc đầu năm <strong>01/01/2026</strong>.
        </div>
      </div>

      <!-- Aspect x Label Matrix -->
      <div class="metric-card lg:col-span-2">
        <h2 class="text-base font-semibold flex items-center gap-2 mb-3">
          <span>🧩</span> Ma trận chéo: Khía cạnh (Aspect) × Nhãn (Label)
        </h2>
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left">
            <thead class="text-[var(--muted)] border-b border-slate-700 bg-slate-800/50">
              <tr>
                <th class="py-2.5 px-3 font-semibold">Khía cạnh thực thể</th>
                <th class="py-2.5 px-3 font-semibold text-blue-400 text-center">Trung tính</th>
                <th class="py-2.5 px-3 font-semibold text-amber-400 text-center">Hỏi đáp</th>
                <th class="py-2.5 px-3 font-semibold text-emerald-400 text-center">Tích cực</th>
                <th class="py-2.5 px-3 font-semibold text-slate-400 text-center">Không liên quan</th>
                <th class="py-2.5 px-3 font-semibold text-right">Tổng bài</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
              <tr class="hover:bg-slate-800/30">
                <td class="py-2 px-3 font-medium text-slate-200">Chương trình đào tạo</td>
                <td class="py-2 px-3 text-center font-bold text-blue-400">122</td>
                <td class="py-2 px-3 text-center font-medium text-amber-400">9</td>
                <td class="py-2 px-3 text-center font-bold text-emerald-400">3</td>
                <td class="py-2 px-3 text-center text-slate-400">12</td>
                <td class="py-2 px-3 text-right font-bold">146</td>
              </tr>
              <tr class="hover:bg-slate-800/30">
                <td class="py-2 px-3 font-medium text-slate-200">Thi cử & Điểm số</td>
                <td class="py-2 px-3 text-center font-bold text-blue-400">114</td>
                <td class="py-2 px-3 text-center font-medium text-amber-400">4</td>
                <td class="py-2 px-3 text-center font-bold text-emerald-400">4</td>
                <td class="py-2 px-3 text-center text-slate-400">17</td>
                <td class="py-2 px-3 text-right font-bold">139</td>
              </tr>
              <tr class="hover:bg-slate-800/30">
                <td class="py-2 px-3 font-medium text-slate-200">Giảng viên</td>
                <td class="py-2 px-3 text-center font-bold text-blue-400">115</td>
                <td class="py-2 px-3 text-center font-medium text-amber-400">12</td>
                <td class="py-2 px-3 text-center font-bold text-emerald-400">4</td>
                <td class="py-2 px-3 text-center text-slate-400">6</td>
                <td class="py-2 px-3 text-right font-bold">137</td>
              </tr>
              <tr class="hover:bg-slate-800/30">
                <td class="py-2 px-3 font-medium text-slate-200">Thủ tục hành chính (DAA)</td>
                <td class="py-2 px-3 text-center font-bold text-blue-400">54</td>
                <td class="py-2 px-3 text-center font-medium text-amber-400">2</td>
                <td class="py-2 px-3 text-center font-medium text-slate-500">0</td>
                <td class="py-2 px-3 text-center text-slate-400">6</td>
                <td class="py-2 px-3 text-right font-bold">62</td>
              </tr>
              <tr class="hover:bg-slate-800/30">
                <td class="py-2 px-3 font-medium text-slate-200">Đoàn - Hội sinh viên</td>
                <td class="py-2 px-3 text-center font-bold text-blue-400">54</td>
                <td class="py-2 px-3 text-center font-medium text-amber-400">2</td>
                <td class="py-2 px-3 text-center font-medium text-slate-500">0</td>
                <td class="py-2 px-3 text-center text-slate-400">3</td>
                <td class="py-2 px-3 text-right font-bold">59</td>
              </tr>
              <tr class="hover:bg-slate-800/30">
                <td class="py-2 px-3 font-medium text-slate-200">Cơ sở vật chất</td>
                <td class="py-2 px-3 text-center font-bold text-blue-400">43</td>
                <td class="py-2 px-3 text-center font-medium text-amber-400">3</td>
                <td class="py-2 px-3 text-center font-bold text-emerald-400">1</td>
                <td class="py-2 px-3 text-center text-slate-400">5</td>
                <td class="py-2 px-3 text-right font-bold">52</td>
              </tr>
              <tr class="hover:bg-slate-800/30">
                <td class="py-2 px-3 font-medium text-slate-200">Học phí & Học bổng</td>
                <td class="py-2 px-3 text-center font-bold text-blue-400">35</td>
                <td class="py-2 px-3 text-center font-medium text-slate-500">0</td>
                <td class="py-2 px-3 text-center font-medium text-slate-500">0</td>
                <td class="py-2 px-3 text-center text-slate-400">3</td>
                <td class="py-2 px-3 text-right font-bold">38</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

    <!-- Interactive Data Explorer Section -->
    <section class="metric-card">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <div>
          <h2 class="text-base font-semibold flex items-center gap-2">
            <span>🔍</span> Trình Khám phá & Kiểm tra Mẫu Dữ liệu Thực tế
          </h2>
          <p class="text-xs text-[var(--muted)] mt-0.5">Lọc nhanh theo nhãn, khía cạnh và tìm kiếm từ khóa trong bài đăng đã ẩn danh</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <!-- Filter Label -->
          <select id="filterLabel" onchange="applyFilters()" class="bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500">
            <option value="all">Tất cả nhãn</option>
            <option value="trung_tinh">Trung tính</option>
            <option value="hoi_dap">Hỏi đáp</option>
            <option value="tich_cuc">Tích cực</option>
            <option value="khong_lien_quan">Không liên quan</option>
          </select>
          <!-- Search input -->
          <input id="searchInput" type="text" placeholder="Tìm kiếm từ khóa..." oninput="applyFilters()" class="bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500 w-48" />
        </div>
      </div>

      <!-- Data Table -->
      <div class="overflow-x-auto rounded-lg border border-slate-800">
        <table class="w-full text-xs text-left" id="sampleTable">
          <thead class="text-[var(--muted)] border-b border-slate-800 bg-slate-800/60 uppercase text-[11px] tracking-wider">
            <tr>
              <th class="py-2.5 px-3 w-36">Post ID</th>
              <th class="py-2.5 px-3 w-32">Nhãn</th>
              <th class="py-2.5 px-3 w-40">Khía cạnh (Aspects)</th>
              <th class="py-2.5 px-3">Nội dung bài viết (Đã ẩn danh)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800" id="tableBody">
            <!-- Rendered by JS -->
          </tbody>
        </table>
      </div>
      <div class="flex items-center justify-between mt-3 text-xs text-[var(--muted)]">
        <span id="recordCount">Đang tải dữ liệu...</span>
        <span class="text-[11px]">Hiển thị tối đa 50 kết quả phù hợp</span>
      </div>
    </section>

  </div>

  <script>
    const allSamples = {json.dumps(samples, ensure_ascii=False)};

    function getLabelBadge(lbl) {{
      const map = {{
        'khong_lien_quan': '<span class="badge badge-khong-lien-quan">Không liên quan</span>',
        'trung_tinh': '<span class="badge badge-trung-tinh">Trung tính</span>',
        'hoi_dap': '<span class="badge badge-hoi-dap">Hỏi đáp</span>',
        'tich_cuc': '<span class="badge badge-tich-cuc">Tích cực</span>',
        'tieu_cuc': '<span class="badge badge-tieu-cuc">Tiêu cực</span>'
      }};
      return map[lbl] || `<span class="badge bg-slate-700">${{lbl}}</span>`;
    }}

    function getAspectBadges(asp) {{
      if (!asp || asp === 'nan') return '<span class="text-slate-500 text-[11px]">—</span>';
      return asp.split('|').filter(Boolean).map(a => `<span class="badge badge-aspect mr-1 mb-1">${{a}}</span>`).join('');
    }}

    function applyFilters() {{
      const labelFilter = document.getElementById('filterLabel').value;
      const searchKey = document.getElementById('searchInput').value.toLowerCase().trim();

      const filtered = allSamples.filter(item => {{
        const matchLabel = (labelFilter === 'all') || (item.label === labelFilter);
        const matchSearch = (!searchKey) || 
          (item.text && item.text.toLowerCase().includes(searchKey)) ||
          (item.id && item.id.includes(searchKey)) ||
          (item.aspects && item.aspects.toLowerCase().includes(searchKey));
        return matchLabel && matchSearch;
      }});

      const tbody = document.getElementById('tableBody');
      const displayList = filtered.slice(0, 50);

      if (displayList.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-6 text-slate-500">Không tìm thấy bài viết nào phù hợp bộ lọc</td></tr>';
      }} else {{
        tbody.innerHTML = displayList.map(item => `
          <tr class="hover:bg-slate-800/40 transition-colors">
            <td class="py-2.5 px-3 font-mono text-slate-400">${{item.id}}</td>
            <td class="py-2.5 px-3">${{getLabelBadge(item.label)}}</td>
            <td class="py-2.5 px-3">${{getAspectBadges(item.aspects)}}</td>
            <td class="py-2.5 px-3 text-slate-200 leading-relaxed">${{item.text || '<em class="text-slate-500">(bài viết không có text)</em>'}}</td>
          </tr>
        `).join('');
      }}

      document.getElementById('recordCount').innerText = `Tìm thấy ${{filtered.length}} / ${{allSamples.length}} bài viết mẫu`;
    }}

    // Initial render
    document.addEventListener('DOMContentLoaded', applyFilters);
  </script>
</body>
</html>
"""

# Write to project folder
out_project = "dashboard.html"
with open(out_project, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Generated dashboard at {{out_project}}")

# Write to artifact folder
artifact_dir = r"C:\Users\admin\.gemini\antigravity\brain\ece4c7c1-19aa-43ce-a06e-3d39231ec0d8"
out_artifact = os.path.join(artifact_dir, "dashboard.html")
with open(out_artifact, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Generated artifact dashboard at {{out_artifact}}")

