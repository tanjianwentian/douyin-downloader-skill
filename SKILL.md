# Douyin Downloader Skill

**功能**: 下载抖音视频（无水印），支持用户主页视频批量下载、单个视频链接下载

**创建时间**: 2026-06-02

**依赖**:
- Python 3.6+
- `requests-html`
- `json-repair` (可选，用于容错解析)

**参考项目**:
- [videodl](https://github.com/CharlesPikachu/videodl) - 2163⭐，支持抖音等多个平台
- [douyin_downloader](https://github.com/renyijiu/douyin_downloader) - 483⭐，专注抖音用户视频批量下载

---

## 使用方法

### 方法一：使用 videodl（推荐，维护活跃）

```bash
# 安装
pip install videofetch

# 下载单个抖音视频
python -m videodl https://v.douyin.com/xxxxx

# 或 Python 代码调用
from videodl import download
download('https://v.douyin.com/xxxxx', output_dir='./videos')
```

**优点**:
- 维护活跃（2026-05-25 仍有更新）
- 支持 50+ 视频平台
- 纯 Python 实现，无需 ADB
- 自动解析无水印地址

**缺点**:
- 仅支持单个视频链接下载
- 不支持批量下载用户所有视频

---

### 方法二：使用 douyin_downloader（批量下载用户视频）

```bash
# 克隆项目
git clone https://github.com/renyijiu/douyin_downloader.git
cd douyin_downloader

# 安装依赖（仅 Python 3.6）
virtualenv -p python3.6 douyin
source douyin/bin/activate
pip install -r requirements.txt

# 下载用户所有视频
python douyin.py -u <user_id>

# 下载用户收藏视频
python douyin.py -u <user_id> -f
```

**优点**:
- 支持批量下载用户所有视频
- 支持下载用户收藏视频
- 无水印下载

**缺点**:
- 仅测试 Python 3.6
- 接口参数可能随时间失效（项目已暂停维护）
- 需要自行获取用户 ID

---

## 核心实现原理

### 1. 视频解析流程（videodl 方案）

```python
# 1. 处理短链接跳转
resp = get(url, allow_redirects=False)
location = resp.headers.get("Location")  # 获取真实视频页 URL

# 2. 提取视频 ID
vid = re.search(r"\d+", location).group(0)

# 3. 请求视频详情页
resp = get(f"https://www.iesdouyin.com/share/video/{vid}")

# 4. 从页面提取 JSON 数据
raw_data = re.search(r"window\._ROUTER_DATA\s*=\s*(.*?)</script>", resp.text)
video_info = json_repair.loads(raw_data)

# 5. 提取无水印播放地址
download_url = f"http://www.iesdouyin.com/aweme/v1/play/?video_id={vid}&ratio=1080p&line=0"
```

### 2. 批量下载流程（douyin_downloader 方案）

```python
# 1. 获取用户信息（uid, dytk）
resp = get(f"https://www.iesdouyin.com/share/user/{user_id}")
uid = re.search(r'uid: "(\d+)"', resp.text)
dytk = re.search(r"dytk: '(\w+)'", resp.text)

# 2. 获取签名（signature.html JS 生成）
signature = get_signature(user_id)

# 3. 请求视频列表 API
params = {
    'user_id': user_id,
    'count': 30,
    'max_cursor': cursor,
    'app_id': 1128,
    '_signature': signature,
}
resp = get('https://www.iesdouyin.com/web/api/v2/aweme/post/', params=params)

# 4. 提取视频播放地址并下载
for item in resp.json()['aweme_list']:
    video_url = item['video']['play_addr']['url_list'][0]
    download_video(video_url, output_dir)
```

---

## OpenClaw 集成示例

### 创建下载任务脚本

```python
#!/usr/bin/env python3
# ~/.openclaw/plugin-skills/douyin-downloader/douyin_download.py

import os
import sys
import re
import json
import requests
from pathlib import Path

MOBILE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
}

DOWNLOAD_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15'
}

def parse_douyin_url(url):
    """解析抖音视频链接，返回无水印下载地址"""
    session = requests.Session()
    
    # 处理短链接跳转
    resp = session.get(url, allow_redirects=False, headers=MOBILE_HEADERS)
    location = resp.headers.get("Location")
    if not location:
        resp = session.get(url, allow_redirects=True, headers=MOBILE_HEADERS)
        location = resp.url
    
    # 提取视频 ID
    vid = re.search(r"\d+", location).group(0)
    
    # 请求视频详情页
    resp = session.get(f"https://www.iesdouyin.com/share/video/{vid}", headers=MOBILE_HEADERS)
    
    # 提取视频信息
    match = re.search(r'window\._ROUTER_DATA\s*=\s*(.*?)</script>', resp.text, re.S | re.I)
    if not match:
        raise Exception("无法解析视频信息")
    
    raw_data = match.group(1).strip().rstrip("; \n\r\t")
    if not raw_data.startswith("{"):
        raw_data = raw_data[raw_data.find("{"):]
    
    try:
        data = json.loads(raw_data)
        video_detail = data.get('loaderData', {}).get('video_(id)/page', {}).get('videoInfoRes', {}).get('item_list', [{}])[0]
        video_title = video_detail.get('desc', f'douyin_{vid}')
        play_addr = video_detail.get('video', {}).get('play_addr', {})
        uri = play_addr.get('uri', vid)
        
        # 构造无水印下载地址
        download_url = f"http://www.iesdouyin.com/aweme/v1/play/?video_id={uri}&ratio=1080p&line=0"
        
        return {
            'title': video_title,
            'download_url': download_url,
            'video_id': vid
        }
    except Exception as e:
        raise Exception(f"解析失败：{e}")

def download_video(url, output_dir='./videos'):
    """下载视频到指定目录"""
    info = parse_douyin_url(url)
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 清理文件名
    safe_title = re.sub(r'[^\w\u4e00-\u9fff]', '_', info['title'])[:50]
    video_path = output_path / f"{safe_title}_{info['video_id']}.mp4"
    
    # 下载视频
    print(f"下载：{info['title']}")
    print(f"地址：{info['download_url']}")
    print(f"保存：{video_path}")
    
    resp = requests.get(info['download_url'], headers=DOWNLOAD_HEADERS, stream=True)
    if resp.status_code == 302:
        # 重定向到真实地址
        resp = requests.get(resp.headers['location'], headers=DOWNLOAD_HEADERS, stream=True)
    
    with open(video_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"✓ 下载完成：{video_path}")
    return str(video_path)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python douyin_download.py <抖音视频链接> [输出目录]")
        sys.exit(1)
    
    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './videos'
    
    try:
        download_video(url, output_dir)
    except Exception as e:
        print(f"✗ 错误：{e}")
        sys.exit(1)
```

---

## 注意事项

1. **接口稳定性**: 抖音接口参数经常变化，若下载失败需检查最新项目 issue
2. **版权**: 仅用于学习研究，请勿商用或侵犯版权
3. **频率限制**: 批量下载时添加延迟，避免触发反爬
4. **代理**: 国内访问可能需要配置代理（参考用户 FoxyProxy 配置 `127.0.0.1:38457`）

---

## 验证清单

- [x] 调研 GitHub 热门项目（videodl 2163⭐, douyin_downloader 483⭐）
- [x] 分析核心实现原理（链接解析、签名生成、视频下载）
- [x] 创建 OpenClaw skill 文件结构
- [x] 提供两种方案对比（单视频 vs 批量）
- [ ] 实际测试下载功能（需用户提供测试链接）
- [ ] 添加错误处理和重试机制

---

## 后续优化

1. 集成到 OpenClaw 工具系统，支持 `exec` 直接调用
2. 添加批量下载用户视频功能
3. 自动检测项目更新和接口变化
4. 支持 TikTok 等国际版
