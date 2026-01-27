import requests
from bs4 import BeautifulSoup
import datetime
import re

# --- カラー・記号設定 ---
C_NORMAL = "#C0FFC0" # 平常
C_WARN = "#FF8C00"   # オレンジ
C_GRAY = "#888888"   # 取得不能

def fetch_soup(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = res.apparent_encoding
        return BeautifulSoup(res.text, 'html.parser')
    except: return None

def get_jr_line_status(url):
    """
    JR北海道の個別路線ページから「当日分」のみを抽出して判定する
    """
    soup = fetch_soup(url)
    if not soup: return {"status": "取得不能", "mark": "？", "level": C_GRAY, "detail": "接続エラー"}
    
    # 1. 「当日分」という見出し(h3)を探す
    today_header = soup.find('h3', string=re.compile("当日分"))
    
    if not today_header:
        # 見出しが見つからない場合は念のため全体で判定
        target_text = re.sub(r'\s+', '', soup.get_text())
    else:
        # 2. 「当日分」見出しの次にある詳細ボックス(div等)を取得
        # JRのサイト構造上、h3の次の要素に運行情報のテーブルやリストが入る
        today_section = today_header.find_next_sibling()
        target_text = re.sub(r'\s+', '', today_section.get_text()) if today_section else ""

    # 3. 指定のフレーズが「当日分」エリアにあるか判定
    target_phrase = "現在、遅れに関する情報はありません。"
    
    if target_phrase in target_text:
        return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "平常通り運転しています"}
    else:
        return {"status": "運休・遅延", "mark": "△", "level": C_WARN, "detail": "当日分の運休・遅延情報があります。"}

# --- 他の交通機関（これまでのロジックを維持） ---

def get_subway_status():
    soup = fetch_soup("https://operationstatus.city.sapporo.jp/unkojoho/")
    if not soup: return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "取得不可(平常)"}
    text = re.sub(r'\s+', '', soup.get_text())
    if any(x in text for x in ["現在、情報はございません", "運行情報はありません", "平常"]):
        return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "平常通り運転中"}
    return {"status": "運休・遅延", "mark": "△", "level": C_WARN, "detail": "地下鉄線内でダイヤが乱れています"}

def get_tram_status():
    soup = fetch_soup("https://www.stsp.or.jp/business/streetcar/unko/")
    if not soup: return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "取得不可(平常)"}
    text = re.sub(r'\s+', '', soup.get_text())
    if any(x in text for x in ["平常どおり", "通常どおり", "ありません"]):
        return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "平常通り運転中"}
    return {"status": "運休・遅延", "mark": "△", "level": C_WARN, "detail": "運行状況にご注意ください"}

def get_bus_status():
    soup = fetch_soup("https://www.chuo-bus.co.jp/")
    if not soup: return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "平常とみなします"}
    text = soup.get_text()
    if any(x in text for x in ["運休", "遅延", "遅れ", "見合わせ"]):
        return {"status": "一部運休・大幅遅延", "mark": "△", "level": C_WARN, "detail": "遅れ・運休が出ています"}
    return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "平常通り運転中"}

def get_highway_status():
    soup = fetch_soup("https://roadway.yahoo.co.jp/traffic/area/1/highway")
    if not soup: return {"status": "取得不能", "mark": "？", "level": C_GRAY, "detail": "情報取得不可"}
    text = soup.get_text()
    if "通行止" in text:
        return {"status": "一部通行止", "mark": "△", "level": C_WARN, "detail": "区間規制または通行止めがあります"}
    return {"status": "開通", "mark": "◯", "level": C_NORMAL, "detail": "規制情報はありません"}

# --- HTML生成 (以前のレイアウト・JSをそのまま維持) ---
def generate():
    jr_chitose = get_jr_line_status("https://www3.jrhokkaido.co.jp/webunkou/senku.html?id=03")
    jr_airport = get_jr_line_status("https://www3.jrhokkaido.co.jp/webunkou/senku.html?id=02")
    jr_gakuen  = get_jr_line_status("https://www3.jrhokkaido.co.jp/webunkou/senku.html?id=04")
    sub, tram, bus, hw = get_subway_status(), get_tram_status(), get_bus_status(), get_highway_status()

    sections = [
        {"title": "JR北海道", "items": [
            {"id": "jr_h", "name": "函館・千歳線", "d": jr_chitose, "color": "#44AF35"},
            {"id": "jr_a", "name": "エアポート", "d": jr_airport, "color": "#44AF35"},
            {"id": "jr_g", "name": "学園都市線", "d": jr_gakuen, "color": "#44AF35"}
        ]},
        {"title": "札幌市営", "items": [
            {"id": "sub_n", "name": "南北線", "d": sub, "color": "#008000"},
            {"id": "sub_z", "name": "東西線", "d": sub, "color": "#FFC000"},
            {"id": "sub_h", "name": "東豊線", "d": sub, "color": "#4080FF"},
            {"id": "tram", "name": "札幌市電", "d": tram, "color": "#C0C0C0"}
        ]},
        {"title": "路線バス", "items": [
            {"id": "bus_jr", "name": "JR北海道バス", "d": bus, "color": "#4040FF"},
            {"id": "bus_ch", "name": "中央バス", "d": bus, "color": "#FF4040"},
            {"id": "bus_jo", "name": "じょうてつ", "d": bus, "color": "#FF8000"}
        ]},
        {"title": "高速道路", "items": [
            {"id": "hw_s", "name": "札樽道・後志道", "d": hw, "color": "#43AF35"},
            {"id": "hw_d", "name": "道央道・道東道", "d": hw, "color": "#43AF35"}
        ]}
    ]

    now_obj = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    now = now_obj.strftime("%Y/%m/%d %H:%M")

    html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=M+PLUS+2:wght@700&family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #000; color: #fff; font-family: 'Noto Sans JP', sans-serif; overflow-x: hidden; }}
        .header {{ background: #C0FFC0; color: #000; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; border-bottom: 2px solid #000; }}
        .header-title {{ font-family: 'M PLUS 2', sans-serif; font-size: 1.5rem; }}
        .header-time {{ font-family: 'M PLUS 2', sans-serif; font-size: 1.1rem; font-weight: bold; }}
        .board {{ display: grid; grid-template-columns: 1fr; gap: 0; width: 100%; }}
        @media (min-width: 1000px) {{ .board {{ grid-template-columns: 1fr 1fr; gap: 0 10px; padding: 5px; }} }}
        details {{ border-bottom: 1px solid #333; width: 100%; }}
        summary {{ background: #1a1a1a; color: #C0FFC0; padding: 12px 20px; font-weight: bold; cursor: pointer; list-style: none; position: relative; border-bottom: 1px solid #333; }}
        summary::after {{ content: '▼'; position: absolute; right: 20px; font-size: 0.8rem; transition: 0.3s; }}
        details[open] summary::after {{ transform: rotate(180deg); }}
        .row {{ display: flex; align-items: center; padding: 12px 15px; background: #000; border-bottom: 1px solid #222; min-height: 90px; }}
        .line-box {{ width: 200px; display: flex; align-items: center; gap: 12px; flex-shrink: 0; }}
        .line-bar {{ width: 10px; height: 50px; border-radius: 2px; }}
        .line-name {{ font-size: 1.4rem; font-weight: 900; line-height: 1.2; letter-spacing: -0.5px; }}
        .symbol-box {{ width: 60px; text-align: center; font-size: 2.5rem; font-weight: bold; flex-shrink: 0; }}
        .info-box {{ flex: 1; padding-left: 20px; }}
        .status-text {{ font-size: 1.2rem; font-weight: bold; margin-bottom: 2px; }}
        .detail-text {{ font-size: 0.85rem; color: #aaa; }}
        #admin-panel {{ display: none; background: #111; padding: 20px; border: 3px solid #C0FFC0; margin: 10px; border-radius: 8px; }}
        .admin-item {{ margin-bottom: 12px; }}
        .admin-label {{ display: block; color: #C0FFC0; font-size: 0.9rem; font-weight: bold; margin-bottom: 4px; }}
        .admin-input {{ width: 100%; background: #222; color: #fff; border: 1px solid #444; padding: 10px; border-radius: 4px; font-size: 1rem; }}
        .save-btn {{ background: #C0FFC0; color: #000; padding: 15px; border: none; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.1rem; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-title">札幌周辺 交通情報のご案内</div>
        <div class="header-time">{now}</div>
    </div>
    <div id="admin-panel">
        <h3 style="color:#C0FFC0; margin-bottom:15px;">備考手動修正モード</h3>
        <div id="form-container"></div>
        <button class="save-btn" onclick="saveManual()">保存して更新</button>
    </div>
    <div class="board">"""

    for sec in sections:
        html_content += f'<details open><summary>{sec["title"]}</summary>'
        for item in sec["items"]:
            d = item["d"]
            html_content += f"""
            <div class="row" id="row-{item['id']}">
                <div class="line-box">
                    <div class="line-bar" style="background:{item['color']};"></div>
                    <div class="line-name">{item["name"]}</div>
                </div>
                <div class="symbol-box" style="color:{d['level']};">{d['mark']}</div>
                <div class="info-box">
                    <div class="status-text" style="color:{d['level']};">{d['status']}</div>
                    <div class="detail-text" id="text-{item['id']}">{d['detail']}</div>
                </div>
            </div>"""
        html_content += '</details>'

    html_content += """
    </div>
    <script>
        const DB_KEY = 'sap_traffic_v11';
        const LAST_RESET_KEY = 'sap_traffic_last_reset';
        function checkDailyReset() {
            const now = new Date();
            let resetTime = new Date();
            resetTime.setHours(3, 0, 0, 0);
            if (now < resetTime) { resetTime.setDate(resetTime.getDate() - 1); }
            const lastReset = localStorage.getItem(LAST_RESET_KEY);
            const resetTimestamp = resetTime.getTime().toString();
            if (!lastReset || lastReset !== resetTimestamp) {
                localStorage.removeItem(DB_KEY);
                localStorage.setItem(LAST_RESET_KEY, resetTimestamp);
                return true;
            }
            return false;
        }
        function checkHash() {
            document.getElementById('admin-panel').style.display = (window.location.hash === '#admin') ? 'block' : 'none';
        }
        function saveManual() {
            const notes = {};
            document.querySelectorAll('.admin-input').forEach(i => { notes[i.dataset.id] = i.value; });
            localStorage.setItem(DB_KEY, JSON.stringify(notes));
            window.location.hash = ''; window.location.reload();
        }
        window.onload = () => {
            checkDailyReset();
            const saved = JSON.parse(localStorage.getItem(DB_KEY) || '{}');
            const form = document.getElementById('form-container');
            document.querySelectorAll('.row').forEach(row => {
                const id = row.id.replace('row-', '');
                const name = row.querySelector('.line-name').innerText;
                const detailEl = document.getElementById('text-' + id);
                form.innerHTML += `<div class="admin-item"><label class="admin-label">${name}</label><input class="admin-input" data-id="${id}" value="${saved[id] || ''}"></div>`;
                if (saved[id] && saved[id].trim() !== "") {
                    detailEl.innerText = saved[id];
                    detailEl.style.color = "#FFD700";
                    detailEl.style.fontWeight = "bold";
                }
            });
            checkHash();
        };
        window.onhashchange = checkHash;
    </script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__": generate()
