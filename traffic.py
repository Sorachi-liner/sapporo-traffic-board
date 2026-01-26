import requests
from bs4 import BeautifulSoup
import datetime
import re

# --- カラー設定 ---
C_NORMAL = "#C0FFC0" 
C_WARN = "#FF8C00"   
C_STOP = "#FF3333"   
C_GRAY = "#888888"   

def fetch_soup(url):
    try:
        res = requests.get(url, timeout=10)
        res.encoding = res.apparent_encoding
        text = re.sub(r'>\s+<', '><', res.text)
        return BeautifulSoup(text, 'html.parser')
    except: return None

# --- 運行情報取得ロジック ---

def get_jr_status():
    soup = fetch_soup("https://www3.jrhokkaido.co.jp/webunkou/area_spo.html")
    if not soup: return {"status": "取得不能", "mark": "？", "level": C_GRAY, "detail": "サイトに接続できません"}
    text = soup.get_text()
    if "平常通り" in text or "運行情報はありません" in text:
        return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "平常通り運転しています"}
    return {"status": "運休・遅延", "mark": "△", "level": C_WARN, "detail": "列車に運休や遅れが発生しています"}

def get_subway_status():
    soup = fetch_soup("https://operationstatus.city.sapporo.jp/unkojoho/")
    if not soup: return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "取得不能につき平常とみなします"}
    text = soup.get_text()
    if any(x in text for x in ["平常", "通常", "運行情報はありません", "現在、情報はございません"]):
        return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "平常通り運転中"}
    if any(x in text for x in ["ダイヤ乱れ", "遅延", "見合わせ", "運休"]):
        return {"status": "運休・遅延", "mark": "△", "level": C_WARN, "detail": "地下鉄線内でダイヤが乱れています"}
    return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "平常通り運転中"}

def get_tram_status():
    soup = fetch_soup("https://www.stsp.or.jp/business/streetcar/unko/")
    if not soup: return {"status": "平常運転", "mark": "◯", "level": C_NORMAL, "detail": "平常とみなします"}
    text = soup.get_text()
    if any(x in text for x in ["平常", "通常", "ありません", "ございません"]):
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

# --- HTML生成 ---
def generate():
    jr, sub, tram, bus, hw = get_jr_status(), get_subway_status(), get_tram_status(), get_bus_status(), get_highway_status()

    sections = [
        {"title": "JR北海道", "items": [
            {"id": "jr_h", "name": "函館・千歳線", "d": jr, "color": "#44AF35"},
            {"id": "jr_a", "name": "エアポート", "d": jr, "color": "#44AF35"},
            {"id": "jr_g", "name": "学園都市線", "d": jr, "color": "#44AF35"}
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

    # 日本時間での時刻取得
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
        <div class="header-title">札幌市周辺 現在の道路情報</div>
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

        // 毎日午前3時にリセットする関数
        function checkDailyReset() {
            const now = new Date();
            // 今日の午前3時のタイムスタンプを作成
            let resetTime = new Date();
            resetTime.setHours(3, 0, 0, 0);

            // 現在時刻が3時を過ぎているかどうか
            // もし3時前なら、リセット基準は「昨日の3時」になる
            if (now < resetTime) {
                resetTime.setDate(resetTime.getDate() - 1);
            }

            const lastReset = localStorage.getItem(LAST_RESET_KEY);
            const resetTimestamp = resetTime.getTime().toString();

            // 最後にリセットした記録がない、または記録がリセット基準時間より古い場合
            if (!lastReset || lastReset !== resetTimestamp) {
                localStorage.removeItem(DB_KEY);
                localStorage.setItem(LAST_RESET_KEY, resetTimestamp);
                return true; // リセット実行
            }
            return false;
        }

        function checkHash() {
            document.getElementById('admin-panel').style.display = (window.location.hash === '#admin') ? 'block' : 'none';
        }

        function saveManual() {
            const notes = {};
            document.querySelectorAll('.admin-input').forEach(i => {
                notes[i.dataset.id] = i.value;
            });
            localStorage.setItem(DB_KEY, JSON.stringify(notes));
            window.location.hash = '';
            window.location.reload();
        }

        window.onload = () => {
            const hasReset = checkDailyReset();
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
            if (hasReset) console.log("Daily reset at 3:00 AM executed.");
        };

        window.onhashchange = checkHash;
    </script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__": generate()

