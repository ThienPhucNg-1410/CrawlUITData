import re

with open('dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update initial static numbers in Crawl Progress Section
content = content.replace('0 / 1,500 bài', '1,500 / 1,500 bài')
content = content.replace('0.0% hoàn thành', '100.0% hoàn thành')
content = content.replace('style="width: 0%"', 'style="width: 100%"')
content = content.replace('<span class="text-base font-bold text-emerald-400 font-mono" id="totalCommentsVal">0</span>', '<span class="text-base font-bold text-emerald-400 font-mono" id="totalCommentsVal">5,520</span>')
content = content.replace('<span class="text-base font-bold text-rose-400 font-mono" id="totalReactionsVal">0</span>', '<span class="text-base font-bold text-rose-400 font-mono" id="totalReactionsVal">23,619</span>')
content = content.replace('<span class="text-base font-bold text-sky-400 font-mono" id="totalSharesVal">0</span>', '<span class="text-base font-bold text-sky-400 font-mono" id="totalSharesVal">1,205</span>')
content = content.replace('Đang chạy nền', 'Hoàn tất 100% mục tiêu (1.500 bài)')

# 2. Thay thế Interactive Section bằng giao diện Tab hiện đại
old_section_marker = '<!-- Interactive Data Explorer Section -->'
new_interactive_section = """<!-- Interactive Data Explorer Section -->
    <section class="metric-card">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <div>
          <h2 class="text-base font-semibold flex items-center gap-2">
            <span>🔍</span> Trình Khám Phá & Đọc Dữ Liệu Thực Tế
          </h2>
          <p class="text-xs text-[var(--muted)] mt-0.5">Duyệt và tìm kiếm trực tiếp 1.500 bài viết gốc hoặc 5.520 bình luận vừa thu thập</p>
        </div>
        
        <!-- Tab selector -->
        <div class="flex items-center gap-2 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          <button id="tabBtnPosts" onclick="switchTab('posts')" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all bg-indigo-600 text-white shadow-sm flex items-center gap-1.5">
            <span>📋</span> 1.500 Bài Viết Gốc
          </button>
          <button id="tabBtnComments" onclick="switchTab('comments')" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all text-slate-400 hover:text-white flex items-center gap-1.5">
            <span>💬</span> 5.520 Bình Luận
          </button>
          <button id="tabBtnSamples" onclick="switchTab('samples')" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all text-slate-400 hover:text-white flex items-center gap-1.5">
            <span>🎭</span> Mẫu ABSA Gán Nhãn
          </button>
        </div>
      </div>

      <!-- Controls bar -->
      <div class="flex flex-wrap items-center justify-between gap-3 pb-3 mb-3 border-b border-slate-800/80 text-xs">
        <div class="flex items-center gap-2 flex-1 max-w-md">
          <div class="relative w-full">
            <input id="searchInput" type="text" placeholder="Tìm kiếm nội dung, tác giả, ID..." oninput="handleSearch()" class="w-full bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded-lg pl-8 pr-3 py-2 focus:outline-none focus:border-indigo-500" />
            <span class="absolute left-2.5 top-2.5 text-slate-400">🔎</span>
          </div>
        </div>

        <div id="sampleFilterContainer" class="hidden flex items-center gap-2">
          <select id="filterLabel" onchange="applyFilters()" class="bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500">
            <option value="all">Tất cả nhãn</option>
            <option value="trung_tinh">Trung tính</option>
            <option value="hoi_dap">Hỏi đáp</option>
            <option value="tich_cuc">Tích cực</option>
            <option value="khong_lien_quan">Không liên quan</option>
          </select>
        </div>
        
        <div class="text-xs text-slate-400 font-mono" id="recordCount">Đang tải dữ liệu...</div>
      </div>

      <!-- Data Table -->
      <div class="overflow-x-auto rounded-lg border border-slate-800">
        <table class="w-full text-xs text-left" id="mainDataTable">
          <thead class="text-[var(--muted)] border-b border-slate-800 bg-slate-800/60 uppercase text-[11px] tracking-wider" id="tableHeader">
            <!-- Rendered by JS based on current tab -->
          </thead>
          <tbody class="divide-y divide-slate-800" id="tableBody">
            <!-- Rendered by JS -->
          </tbody>
        </table>
      </div>

      <div class="flex items-center justify-between mt-3 text-xs text-[var(--muted)]">
        <span class="text-[11px] text-slate-500">Dữ liệu được cập nhật trực tiếp từ SQLite</span>
        <button onclick="reloadCurrentTab()" class="text-indigo-400 hover:text-indigo-300 font-medium">Làm mới danh sách</button>
      </div>
    </section>
"""

# Tìm điểm cắt từ old_section_marker đến trước `<script>`
parts = content.split(old_section_marker)
if len(parts) == 2:
    before = parts[0]
    after = parts[1]
    # Tìm thẻ <script>
    script_idx = after.find('<script>')
    if script_idx != -1:
        after_script = after[script_idx:]
        content = before + new_interactive_section + '\n  </div>\n\n  ' + after_script

# 3. Thêm các hàm xử lý Tab và load API posts/comments vào script
script_addition = """
    let currentTab = 'posts';
    let currentPostsData = [];
    let currentCommentsData = [];
    let searchDebounceTimer = null;

    function switchTab(tab) {
      currentTab = tab;
      const btnP = document.getElementById('tabBtnPosts');
      const btnC = document.getElementById('tabBtnComments');
      const btnS = document.getElementById('tabBtnSamples');
      const sampleFilter = document.getElementById('sampleFilterContainer');
      const searchInput = document.getElementById('searchInput');

      btnP.className = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ' + (tab === 'posts' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white');
      btnC.className = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ' + (tab === 'comments' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white');
      btnS.className = 'px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ' + (tab === 'samples' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white');

      if (tab === 'samples') {
        sampleFilter.classList.remove('hidden');
        searchInput.placeholder = 'Tìm trong mẫu ABSA...';
        applyFilters();
      } else if (tab === 'comments') {
        sampleFilter.classList.add('hidden');
        searchInput.placeholder = 'Tìm bình luận, người bình luận...';
        loadCommentsData();
      } else {
        sampleFilter.classList.add('hidden');
        searchInput.placeholder = 'Tìm bài viết, tác giả, ID...';
        loadPostsData();
      }
    }

    function handleSearch() {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        if (currentTab === 'samples') {
          applyFilters();
        } else if (currentTab === 'comments') {
          loadCommentsData();
        } else {
          loadPostsData();
        }
      }, 300);
    }

    function reloadCurrentTab() {
      switchTab(currentTab);
    }

    async function loadPostsData() {
      const q = document.getElementById('searchInput').value.trim();
      const th = document.getElementById('tableHeader');
      const tb = document.getElementById('tableBody');
      const rc = document.getElementById('recordCount');

      th.innerHTML = `
        <tr>
          <th class="py-2.5 px-3 w-32">Post ID</th>
          <th class="py-2.5 px-3 w-40">Tác giả</th>
          <th class="py-2.5 px-3 w-20 text-center">Reacts</th>
          <th class="py-2.5 px-3 w-20 text-center">Shares</th>
          <th class="py-2.5 px-3 w-20 text-center">Cmts</th>
          <th class="py-2.5 px-3">Nội dung bài viết (Nguyên bản thô)</th>
          <th class="py-2.5 px-3 w-20 text-center">Link</th>
        </tr>
      `;
      tb.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-400">Đang tải danh sách bài viết từ database...</td></tr>';

      try {
        const url = '/api/posts?limit=100' + (q ? '&search=' + encodeURIComponent(q) : '');
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          currentPostsData = data.posts || [];
          rc.innerText = `Hiển thị ${currentPostsData.length} / ${data.total || 1500} bài viết`;

          if (currentPostsData.length === 0) {
            tb.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-500">Không tìm thấy bài viết nào phù hợp</td></tr>';
            return;
          }

          tb.innerHTML = currentPostsData.map(p => `
            <tr class="hover:bg-slate-800/40 transition-colors">
              <td class="py-2.5 px-3 font-mono text-slate-400 font-semibold">${p.post_id}</td>
              <td class="py-2.5 px-3 font-medium text-indigo-300">${p.author || '<span class="text-slate-500 italic">Ẩn danh</span>'}</td>
              <td class="py-2.5 px-3 text-center text-rose-400 font-bold font-mono">${Number(p.reactions || 0).toLocaleString()}</td>
              <td class="py-2.5 px-3 text-center text-sky-400 font-bold font-mono">${Number(p.shares || 0).toLocaleString()}</td>
              <td class="py-2.5 px-3 text-center text-emerald-400 font-bold font-mono">${Number(p.n_comments || 0).toLocaleString()}</td>
              <td class="py-2.5 px-3 text-slate-200 leading-relaxed max-w-xl break-words">${p.text ? p.text.replace(/\\n/g, '<br/>') : '<em class="text-slate-500">(Không có text)</em>'}</td>
              <td class="py-2.5 px-3 text-center">
                ${p.permalink ? `<a href="${p.permalink}" target="_blank" class="text-blue-400 hover:text-blue-300 font-mono underline text-[11px]">Xem ↗</a>` : '—'}
              </td>
            </tr>
          `).join('');
          return;
        }
      } catch (e) {
        console.log('Error fetching posts:', e);
      }
      tb.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-amber-400">Không thể kết nối API. Hãy kiểm tra server đã chạy tại http://localhost:8088</td></tr>';
    }

    async function loadCommentsData() {
      const q = document.getElementById('searchInput').value.trim();
      const th = document.getElementById('tableHeader');
      const tb = document.getElementById('tableBody');
      const rc = document.getElementById('recordCount');

      th.innerHTML = `
        <tr>
          <th class="py-2.5 px-3 w-32">Comment ID</th>
          <th class="py-2.5 px-3 w-32">Post ID</th>
          <th class="py-2.5 px-3 w-40">Tác giả</th>
          <th class="py-2.5 px-3 w-20 text-center">Thời gian</th>
          <th class="py-2.5 px-3">Nội dung bình luận</th>
        </tr>
      `;
      tb.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-slate-400">Đang tải danh sách bình luận...</td></tr>';

      try {
        const url = '/api/comments?limit=100';
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          let cmts = data.comments || [];
          if (q) {
            const ql = q.toLowerCase();
            cmts = cmts.filter(c => (c.text && c.text.toLowerCase().includes(ql)) || (c.author && c.author.toLowerCase().includes(ql)) || (c.post_id && c.post_id.includes(ql)));
          }
          rc.innerText = `Hiển thị ${cmts.length} bình luận`;

          if (cmts.length === 0) {
            tb.innerHTML = '<tr><td colspan="5" class="text-center py-8 text-slate-500">Không tìm thấy bình luận nào phù hợp</td></tr>';
            return;
          }

          tb.innerHTML = cmts.map(c => `
            <tr class="hover:bg-slate-800/40 transition-colors">
              <td class="py-2.5 px-3 font-mono text-slate-400">${c.comment_id}</td>
              <td class="py-2.5 px-3 font-mono text-indigo-400">${c.post_id}</td>
              <td class="py-2.5 px-3 font-medium text-emerald-300">${c.author || '<span class="text-slate-500 italic">Ẩn danh</span>'}</td>
              <td class="py-2.5 px-3 text-center text-slate-400 text-[11px]">${c.time_raw || '—'}</td>
              <td class="py-2.5 px-3 text-slate-200 leading-relaxed max-w-xl break-words">${c.text ? c.text.replace(/\\n/g, '<br/>') : ''}</td>
            </tr>
          `).join('');
          return;
        }
      } catch (e) {
        console.log('Error fetching comments:', e);
      }
      tb.innerHTML = '<tr><td colspan="5" class="text-center py-6 text-amber-400">Không thể kết nối API.</td></tr>';
    }
"""

# Chèn functions vào sau `<script>`
content = content.replace('<script>', '<script>\n' + script_addition)

# Sửa lại phần khởi tạo
content = content.replace('applyFilters();\n      fetchLiveStats();', 'loadPostsData();\n      fetchLiveStats();')

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated dashboard.html successfully!")

