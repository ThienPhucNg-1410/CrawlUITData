"""
generate_visualizations.py
===========================
Tạo bộ biểu đồ phân tích và biểu diễn dữ liệu cảm xúc UIT Confessions:
1. Cơ cấu 7 sắc thái cảm xúc (Thích, Haha, Buồn, Tim, Thương thương, Wow, Phẫn nộ)
2. Nhiệt đồ (Heatmap) hành vi theo 24 giờ x 7 ngày trong tuần
3. Phân tích khía cạnh chủ đề sinh viên (Aspect-Based Sentiment - ABSA):
   - Học tập & Tín chỉ / Thi cử
   - Cơ sở vật chất & Tiện ích
   - Giảng viên & Đào tạo
   - Tình cảm & Đời sống
4. Biến động cảm xúc theo tháng (Tháng 7 - Tháng 10)
5. Tương quan độ dài bài viết & sắc thái cảm xúc
6. Bảng vàng Top Viral Confessions
7. Dashboard tương tác Plotly HTML
"""

import os
import re
import sys
import json
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Cấu hình Matplotlib hỗ trợ tiếng Việt
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'Tahoma', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid", font="Segoe UI")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOT_DIR = os.path.join(ROOT_DIR, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

DB_PATH = os.path.join(ROOT_DIR, "data", "raw", "raw.sqlite")
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(ROOT_DIR, "uit-confession-sentiment", "data", "raw", "raw.sqlite")
conn = sqlite3.connect(DB_PATH)

posts_df = pd.read_sql_query("""
    SELECT post_id, created_at, reactions, reactions_detail, shares, n_comments, text, author, permalink
    FROM posts 
    WHERE status = 'comments_full'
""", conn)
conn.close()

# Parse datetime
posts_df['created_at'] = pd.to_datetime(posts_df['created_at'], errors='coerce')
posts_df['hour'] = posts_df['created_at'].dt.hour
posts_df['weekday'] = posts_df['created_at'].dt.day_name()
posts_df['weekday_num'] = posts_df['created_at'].dt.weekday  # 0: Thứ 2, 6: Chủ nhật
posts_df['month'] = posts_df['created_at'].dt.to_period('M').astype(str)
posts_df['word_count'] = posts_df['text'].fillna('').apply(lambda x: len(x.split()))

# Parse reactions_detail
def parse_rx(x):
    if not x:
        return {'like': 0, 'love': 0, 'care': 0, 'haha': 0, 'wow': 0, 'sad': 0, 'angry': 0, 'total': 0}
    try:
        data = json.loads(x)
        return {
            'like': data.get('like', 0),
            'love': data.get('love', 0),
            'care': data.get('care', 0),
            'haha': data.get('haha', 0),
            'wow': data.get('wow', 0),
            'sad': data.get('sad', 0),
            'angry': data.get('angry', 0),
            'total': data.get('total', 0)
        }
    except Exception:
        return {'like': 0, 'love': 0, 'care': 0, 'haha': 0, 'wow': 0, 'sad': 0, 'angry': 0, 'total': 0}

rx_series = posts_df['reactions_detail'].apply(parse_rx).apply(pd.Series)
for col in ['like', 'love', 'care', 'haha', 'wow', 'sad', 'angry', 'total']:
    posts_df[col] = rx_series[col].fillna(0).astype(int)

# Gán nhãn chủ đề (Aspect Extraction theo từ khóa)
aspect_keywords = {
    'Học tập & Thi cử': [
        'thi', 'rớt môn', 'qua môn', 'điểm', 'gpa', 'học lại', 'đề khó', 'phúc khảo', 'f', 'tín chỉ', 
        'dkmh', 'đăng ký môn', 'học phí', 'học kỳ', 'đồ án', 'tiểu luận', 'bài tập lớn', 'bttl', 'thực hành',
        'cơ sở dữ liệu', 'csdl', 'giải tích', 'đại số', 'ctdl', 'oop', 'mạng máy tính', 'kiến trúc máy tính'
    ],
    'Cơ sở vật chất & Tiện ích': [
        'wifi', 'mạng', 'thang máy', 'bãi xe', 'gửi xe', 'máy lạnh', 'thư viện', 'ktx', 'ký túc xá', 
        'căn tin', 'nhà vệ sinh', 'wc', 'phòng học', 'tòa e', 'tòa a', 'tòa b', 'tòa c', 'bàn ghế', 'ổ cắm'
    ],
    'Giảng viên & Đào tạo': [
        'thầy', 'cô', 'giảng viên', 'đào tạo', 'phòng đào tạo', 'pđt', 'học vụ', 'quy chế', 'giáo vụ', 
        'cố vấn', 'chấm điểm', 'điểm danh', 'bài giảng', 'slide'
    ],
    'Đời sống & Tình cảm': [
        'crush', 'thích bạn', 'người yêu', 'tỏ tình', 'bạn bè', 'quân sự', 'qs', 'hội trại', 'clb', 
        'câu lạc bộ', 'tân sinh viên', 'k19', 'k20', 'k21', 'k22', 'k18', 'trọ', 'ở ghép', 'tâm sự'
    ]
}

def detect_aspects(text):
    if not isinstance(text, str):
        return 'Chủ đề khác'
    text_lower = text.lower()
    matched = []
    for aspect, kws in aspect_keywords.items():
        pattern = r'\b(' + '|'.join(re.escape(k) for k in kws) + r')\b'
        if re.search(pattern, text_lower):
            matched.append(aspect)
    return matched if matched else ['Chủ đề khác']

posts_df['aspects'] = posts_df['text'].apply(detect_aspects)
posts_df['primary_aspect'] = posts_df['aspects'].apply(lambda x: x[0])

print(f"Loaded {len(posts_df)} posts for visualization.")

# ===================================================================================
# 1. BIỂU ĐỒ CƠ CẤU 7 SẮC THÁI CẢM XÚC (DONUT & BAR CHART)
# ===================================================================================
emotions = ['like', 'haha', 'sad', 'love', 'care', 'wow', 'angry']
labels_vn = ['Thích (Like)', 'Haha (Hài hước)', 'Buồn (Sad)', 'Yêu thích (Love)', 'Thương thương (Care)', 'Wow (Ngạc nhiên)', 'Phẫn nộ (Angry)']
colors = ['#1877F2', '#F7B125', '#5890FF', '#FA3E3E', '#F7B125', '#F7B125', '#E95950']
color_palette = ['#2980b9', '#f39c12', '#3498db', '#e74c3c', '#e67e22', '#9b59b6', '#c0392b']

sums = [posts_df[e].sum() for e in emotions]
total_rx = sum(sums)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle(f"PHÂN BỐ 7 LOẠI BIỂU CẢM TRÊN TOÀN BỘ UIT CONFESSIONS ({len(posts_df):,} BÀI VIẾT & {total_rx:,} LƯỢT TƯƠNG TÁC)", fontsize=16, fontweight='bold', y=0.98)

# Panel 1: Donut Chart
def make_autopct(values):
    def my_autopct(pct):
        return f'{pct:.1f}%' if pct >= 1.5 else ''
    return my_autopct

pie_labels = [l if (s / total_rx * 100) >= 1.5 else '' for l, s in zip(labels_vn, sums)]
wedges, texts, autotexts = ax1.pie(
    sums, labels=pie_labels, autopct=make_autopct(sums), startangle=140,
    pctdistance=0.78, explode=[0.02, 0.02, 0.04, 0.04, 0.08, 0.12, 0.16],
    colors=color_palette, textprops={'fontsize': 10, 'weight': 'bold'}
)
centre_circle = plt.Circle((0, 0), 0.62, fc='white')
ax1.add_artist(centre_circle)
ax1.text(0, 0, f"Tổng cảm xúc\n{total_rx:,}", ha='center', va='center', fontsize=13, fontweight='bold')
ax1.set_title("Tỷ lệ phần trăm các loại biểu cảm (%)", fontsize=13, fontweight='bold', pad=10)
for autotext in autotexts:
    autotext.set_fontweight('bold')
    autotext.set_color('#111827')

ax1.legend(wedges, [f"{l}: {s:,} ({s/total_rx*100:.2f}%)" for l, s in zip(labels_vn, sums)],
           title="Chi Tiết 7 Loại Biểu Cảm", loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=2, fontsize=8.5)

# Panel 2: Horizontal Bar Chart
y_pos = np.arange(len(emotions))
bars = ax2.barh(y_pos, sums, color=color_palette, edgecolor='black', alpha=0.85)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(labels_vn, fontsize=11)
ax2.invert_yaxis()
ax2.set_xlabel("Tổng số lượt biểu cảm", fontsize=11)
ax2.set_title("Số lượng lượt tương tác tuyệt đối", fontsize=13, fontweight='bold', pad=10)

for bar in bars:
    w = bar.get_width()
    ax2.text(w + 2000, bar.get_y() + bar.get_height()/2.0, f"{int(w):,} ({w/total_rx*100:.1f}%)", 
             va='center', fontsize=10, fontweight='bold')
ax2.set_xlim(0, max(sums) * 1.28)

plt.tight_layout()
fig.savefig(os.path.join(PLOT_DIR, "1_emotions_distribution.png"), dpi=300)
plt.close(fig)
print("[✓] Đã tạo 1_emotions_distribution.png (đã sửa không còn dính chữ)")

# ===================================================================================
# 2. NHIỆT ĐỒ (HEATMAP) MẬT ĐỘ ĐĂNG BÀI THEO 24H X 7 NGÀY
# ===================================================================================
weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
weekday_vn = ['Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy', 'Chủ Nhật']

heat_df = posts_df.pivot_table(index='weekday', columns='hour', values='post_id', aggfunc='count', fill_value=0)
heat_df = heat_df.reindex(weekday_order)
heat_df.index = weekday_vn

fig, ax = plt.subplots(figsize=(16, 8))
sns.heatmap(heat_df, cmap='YlGnBu', annot=True, fmt='d', cbar_kws={'label': 'Số lượng bài viết'}, 
            linewidths=0.5, ax=ax, annot_kws={"fontsize": 10})
ax.set_title("NHIỆT ĐỒ MẬT ĐỘ ĐĂNG BÀI UIT CONFESSIONS THEO KHUNG GIỜ VÀ NGÀY TRONG TUẦN", fontsize=15, fontweight='bold', pad=15)
ax.set_xlabel("Khung giờ trong ngày (0h - 23h)", fontsize=12, labelpad=10)
ax.set_ylabel("Ngày trong tuần", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(PLOT_DIR, "2_hourly_weekly_heatmap.png"), dpi=300)
plt.close(fig)
print("[✓] Đã tạo 2_hourly_weekly_heatmap.png")

# ===================================================================================
# 3. MA TRẬN KHÍA CẠNH CHỦ ĐỀ & CẢM XÚC (ASPECT-BASED SENTIMENT ANALYSIS)
# ===================================================================================
# Unnest aspects
aspect_rows = []
for idx, row in posts_df.iterrows():
    for asp in row['aspects']:
        aspect_rows.append({
            'aspect': asp,
            'like': row['like'],
            'haha': row['haha'],
            'sad': row['sad'],
            'love': row['love'],
            'care': row['care'],
            'wow': row['wow'],
            'angry': row['angry'],
            'total': row['total']
        })
asp_df = pd.DataFrame(aspect_rows)
asp_grouped = asp_df.groupby('aspect').agg({
    'total': 'count',
    'haha': 'sum',
    'like': 'sum',
    'sad': 'sum',
    'love': 'sum'
}).rename(columns={'total': 'post_count'})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle("PHÂN TÍCH KHÍA CẠNH CHỦ ĐỀ (ASPECT-BASED SENTIMENT) TẠI UIT CONFESSIONS", fontsize=16, fontweight='bold', y=0.98)

# Panel 1: Số lượng bài viết theo khía cạnh
asp_sorted = asp_grouped.sort_values(by='post_count', ascending=True)
bars = ax1.barh(asp_sorted.index, asp_sorted['post_count'], color='#34495e', edgecolor='black', alpha=0.85)
ax1.set_title("Số lượng bài viết theo khía cạnh", fontsize=13, fontweight='bold', pad=10)
ax1.set_xlabel("Số lượng bài viết", fontsize=11)
for bar in bars:
    w = bar.get_width()
    ax1.text(w + 10, bar.get_y() + bar.get_height()/2.0, f"{int(w):,} bài ({w/len(posts_df)*100:.1f}%)", 
             va='center', fontsize=10, fontweight='bold')
ax1.set_xlim(0, max(asp_sorted['post_count']) * 1.25)

# Panel 2: Tỷ lệ cảm xúc đặc trưng trong từng chủ đề (%)
asp_pct = asp_grouped[['haha', 'sad', 'love', 'like']].div(asp_grouped[['haha', 'sad', 'love', 'like']].sum(axis=1), axis=0) * 100
asp_pct = asp_pct.loc[asp_sorted.index]

asp_pct.plot(kind='barh', stacked=True, color=['#f39c12', '#3498db', '#e74c3c', '#2980b9'], 
             edgecolor='black', alpha=0.9, ax=ax2)
ax2.set_title("Cơ cấu cảm xúc (%) trong từng khía cạnh chủ đề", fontsize=13, fontweight='bold', pad=10)
ax2.set_xlabel("Tỷ lệ % cảm xúc", fontsize=11)
ax2.legend(['Haha (Hài hước)', 'Buồn (Tâm sự)', 'Yêu thích (Tim)', 'Thích (Like)'], loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=4)
ax2.set_xlim(0, 100)

plt.tight_layout()
fig.savefig(os.path.join(PLOT_DIR, "3_aspect_sentiment_matrix.png"), dpi=300)
plt.close(fig)
print("[✓] Đã tạo 3_aspect_sentiment_matrix.png")

# ===================================================================================
# 4. XU HƯỚNG CẢM XÚC BIẾN ĐỘNG THEO THÁNG (TEMPORAL MONTHLY TRENDS)
# ===================================================================================
month_agg = posts_df.groupby('month').agg({
    'post_id': 'count',
    'haha': 'mean',
    'sad': 'mean',
    'love': 'mean',
    'like': 'mean'
}).reset_index()

month_labels = {
    '2026-06': 'Tháng 6/2026\n(Cuối HK2 / Thi HK)',
    '2026-07': 'Tháng 7/2026\n(Hè / Thi lại)',
    '2026-08': 'Tháng 8/2026\n(ĐKMH / Quân sự)',
    '2026-09': 'Tháng 9/2026\n(Tựu trường / Tân SV)',
    '2026-10': 'Tháng 10/2026\n(Đầu HK1)'
}
month_agg['month_label'] = month_agg['month'].map(month_labels)
month_agg = month_agg.dropna(subset=['month_label'])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("XU HƯỚNG BIẾN ĐỘNG CẢM XÚC VÀ SỐ LƯỢNG BÀI THEO CÁC GIAI ĐOẠN HỌC TẬP", fontsize=16, fontweight='bold', y=0.98)

# Panel 1: Số bài viết qua các tháng
palette_5 = ['#27ae60', '#3498db', '#2980b9', '#1f618d', '#154360']
bars = ax1.bar(month_agg['month_label'], month_agg['post_id'], color=palette_5[:len(month_agg)], edgecolor='black', alpha=0.85)
ax1.set_title("Số lượng bài viết theo tháng", fontsize=13, fontweight='bold', pad=10)
ax1.set_ylabel("Số lượng bài viết", fontsize=11)
for bar in bars:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, h + 15, f"{int(h):,} bài", ha='center', va='bottom', fontsize=11, fontweight='bold')
ax1.set_ylim(0, max(month_agg['post_id']) * 1.15)

# Panel 2: Mức độ cảm xúc trung bình trên mỗi bài viết
ax2.plot(month_agg['month_label'], month_agg['haha'], marker='o', linewidth=2.5, color='#f39c12', label='Haha trung bình / bài')
ax2.plot(month_agg['month_label'], month_agg['sad'], marker='s', linewidth=2.5, color='#3498db', label='Buồn trung bình / bài')
ax2.plot(month_agg['month_label'], month_agg['love'], marker='^', linewidth=2.5, color='#e74c3c', label='Tim (Love) trung bình / bài')
ax2.set_title("Cường độ cảm xúc trung bình trên mỗi bài viết", fontsize=13, fontweight='bold', pad=10)
ax2.set_ylabel("Lượt cảm xúc trung bình / bài", fontsize=11)
ax2.legend(fontsize=10)
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
fig.savefig(os.path.join(PLOT_DIR, "4_monthly_sentiment_trends.png"), dpi=300)
plt.close(fig)
print("[✓] Đã tạo 4_monthly_sentiment_trends.png")

# ===================================================================================
# 5. TƯƠNG QUAN ĐỘ DÀI BÀI VIẾT (WORD COUNT) & CẢM XÚC
# ===================================================================================
bins = [0, 20, 50, 100, 200, 500, 2000]
bin_labels = ['< 20 từ\n(Siêu ngắn)', '20-49 từ\n(Ngắn)', '50-99 từ\n(Vừa)', '100-199 từ\n(Dài)', '200-499 từ\n(Tâm sự)', '>= 500 từ\n(Văn tế / Dài tập)']
posts_df['length_bin'] = pd.cut(posts_df['word_count'], bins=bins, labels=bin_labels, right=False)

len_agg = posts_df.groupby('length_bin', observed=False).agg({
    'post_id': 'count',
    'haha': 'mean',
    'sad': 'mean',
    'love': 'mean',
    'reactions': 'mean'
}).reset_index()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("PHÂN TÍCH MỐI QUAN HỆ GIỮA ĐỘ DÀI BÀI VIẾT (WORD COUNT) VÀ SẮC THÁI CẢM XÚC", fontsize=16, fontweight='bold', y=0.98)

# Panel 1: Phân bố số lượng bài theo độ dài
bars = ax1.bar(len_agg['length_bin'], len_agg['post_id'], color=sns.color_palette("mako", len(bin_labels)), edgecolor='black', alpha=0.85)
ax1.set_title("Phân bố số lượng bài viết theo độ dài văn bản", fontsize=13, fontweight='bold', pad=10)
ax1.set_ylabel("Số lượng bài viết", fontsize=11)
for bar in bars:
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, h + 10, f"{int(h):,}", ha='center', va='bottom', fontsize=10, fontweight='bold')
ax1.set_ylim(0, max(len_agg['post_id']) * 1.15)

# Panel 2: Tương tác cảm xúc trung bình theo độ dài
ax2.plot(len_agg['length_bin'], len_agg['haha'], marker='o', linewidth=2.5, color='#f39c12', label='Haha trung bình')
ax2.plot(len_agg['length_bin'], len_agg['sad'], marker='s', linewidth=2.5, color='#3498db', label='Buồn trung bình')
ax2.plot(len_agg['length_bin'], len_agg['love'], marker='^', linewidth=2.5, color='#e74c3c', label='Tim (Love) trung bình')
ax2.set_title("Cảm xúc nhận được theo độ dài bài viết", fontsize=13, fontweight='bold', pad=10)
ax2.set_ylabel("Lượt biểu cảm trung bình / bài", fontsize=11)
ax2.legend(fontsize=10)
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
fig.savefig(os.path.join(PLOT_DIR, "5_text_length_vs_sentiment.png"), dpi=300)
plt.close(fig)
print("[✓] Đã tạo 5_text_length_vs_sentiment.png")

# ===================================================================================
# 6. DASHBOARD PLOTLY HTML TƯƠNG TÁC CAO CẤP
# ===================================================================================
fig_interactive = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "<b>1. Cơ cấu 7 sắc thái cảm xúc</b>",
        "<b>2. Phân bố bài viết theo 4 khía cạnh chủ đề (ABSA)</b>",
        "<b>3. Lượt tương tác theo khung giờ đăng bài (0h - 23h)</b>",
        "<b>4. Tương quan: Độ dài bài viết vs Lượt cảm xúc</b>"
    ),
    specs=[[{"type": "domain"}, {"type": "xy"}],
           [{"type": "xy"}, {"type": "xy"}]]
)

# 1. Donut
fig_interactive.add_trace(
    go.Pie(
        labels=labels_vn,
        values=sums,
        hole=0.55,
        marker=dict(colors=color_palette),
        textinfo='label+percent',
        hoverinfo='label+value+percent'
    ),
    row=1, col=1
)

# 2. Aspect Bar
fig_interactive.add_trace(
    go.Bar(
        x=asp_sorted.index,
        y=asp_sorted['post_count'],
        marker_color='#2c3e50',
        text=asp_sorted['post_count'],
        textposition='auto',
        hoverinfo='x+y'
    ),
    row=1, col=2
)

# 3. Hourly Bar
hourly_counts = posts_df['hour'].value_counts().sort_index()
fig_interactive.add_trace(
    go.Bar(
        x=[f"{h}h" for h in hourly_counts.index],
        y=hourly_counts.values,
        marker_color='#3498db',
        hoverinfo='x+y'
    ),
    row=2, col=1
)

# 4. Scatter Word Count vs Reactions
fig_interactive.add_trace(
    go.Scatter(
        x=posts_df['word_count'],
        y=posts_df['reactions'],
        mode='markers',
        marker=dict(
            size=6,
            color=posts_df['haha'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Haha", len=0.45, y=0.2)
        ),
        text=[f"Post {pid}<br>Từ: {wc}<br>Reactions: {rx}<br>Haha: {ha}" 
              for pid, wc, rx, ha in zip(posts_df['post_id'], posts_df['word_count'], posts_df['reactions'], posts_df['haha'])],
        hoverinfo='text'
    ),
    row=2, col=2
)

fig_interactive.update_layout(
    title_text=f"<b>DASHBOARD TRỰC QUAN HÓA CẢM XÚC UIT CONFESSIONS ({len(posts_df):,} BÀI VIẾT & {total_rx:,} REACTIONS)</b>",
    title_font_size=18,
    showlegend=False,
    height=850,
    template="plotly_white"
)

interactive_html_path = os.path.join(PLOT_DIR, "dashboard_cam_xuc_tuong_tac.html")
fig_interactive.write_html(interactive_html_path, include_plotlyjs="cdn")
print(f"[✓] Đã tạo dashboard HTML tương tác: {interactive_html_path}")

# Đồng bộ file sang thư mục Brain Artifacts
import shutil
BRAIN_PLOT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\f99f17e1-e2b8-4a4b-8d91-8423f1b83827\plots"
os.makedirs(BRAIN_PLOT_DIR, exist_ok=True)
for fname in os.listdir(PLOT_DIR):
    src = os.path.join(PLOT_DIR, fname)
    dst = os.path.join(BRAIN_PLOT_DIR, fname)
    if os.path.isfile(src):
        shutil.copy2(src, dst)
print(f"[✓] Đã đồng bộ toàn bộ biểu đồ vào Artifact Brain: {BRAIN_PLOT_DIR}")

print("\n=======================================================")
print("[THÀNH CÔNG] ĐÃ TẠO TOÀN BỘ 5 BỘ BIỂU ĐỒ VÀ DASHBOARD TƯƠNG TÁC!")
print("=======================================================")
