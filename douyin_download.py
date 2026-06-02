#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音视频下载工具 - 无水印下载
使用方法：python douyin_download.py <抖音视频链接> [输出目录]
"""

import os
import sys
import re
import json
import requests
from pathlib import Path

MOBILE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'DNT': '1',
}

DOWNLOAD_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
    'Accept': '*/*',
    'Connection': 'keep-alive',
}

def parse_douyin_url(url):
    """
    解析抖音视频链接，返回无水印下载地址
    
    Args:
        url: 抖音视频链接（支持 v.douyin.com 短链接）
    
    Returns:
        dict: {'title': str, 'download_url': str, 'video_id': str, 'cover_url': str}
    """
    session = requests.Session()
    session.headers.update(MOBILE_HEADERS)
    
    try:
        # 处理短链接跳转
        resp = session.get(url, allow_redirects=False, timeout=10)
        location = resp.headers.get("Location")
        
        if not location:
            resp = session.get(url, allow_redirects=True, timeout=10)
            location = resp.url
        
        # 提取视频 ID
        vid_match = re.search(r"\d+", location)
        if not vid_match:
            raise Exception("无法从链接中提取视频 ID")
        
        vid = vid_match.group(0)
        
        # 请求视频详情页
        resp = session.get(f"https://www.iesdouyin.com/share/video/{vid}", timeout=10)
        resp.raise_for_status()
        
        # 提取视频信息（从 window._ROUTER_DATA）
        match = re.search(r'window\._ROUTER_DATA\s*=\s*(.*?)</script>', resp.text, re.S | re.I)
        if not match:
            # 尝试备用模式
            match = re.search(r'window\._ROUTER_DATA\s*=\s*({.*?});', resp.text, re.S | re.I)
        
        if not match:
            raise Exception("无法解析页面数据，抖音可能已更新接口")
        
        raw_data = match.group(1).strip().rstrip("; \n\r\t")
        if not raw_data.startswith("{"):
            start_idx = raw_data.find("{")
            if start_idx != -1:
                raw_data = raw_data[start_idx:]
        
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 解析失败：{e}")
        
        # 提取视频详情
        try:
            video_detail = data.get('loaderData', {}).get('video_(id)/page', {}).get('videoInfoRes', {}).get('item_list', [{}])[0]
        except (KeyError, IndexError):
            # 尝试备用路径
            video_detail = data.get('videoInfoRes', {}).get('item_list', [{}])[0] if isinstance(data.get('videoInfoRes'), dict) else {}
        
        if not video_detail:
            raise Exception("无法提取视频信息")
        
        # 提取标题
        video_title = video_detail.get('desc', f'douyin_{vid}')
        
        # 提取视频播放地址
        play_addr = video_detail.get('video', {}).get('play_addr', {})
        uri = play_addr.get('uri', vid)
        
        # 构造无水印下载地址
        download_url = f"http://www.iesdouyin.com/aweme/v1/play/?video_id={uri}&ratio=1080p&line=0"
        
        # 提取封面图
        cover_url = video_detail.get('video', {}).get('cover', {}).get('url_list', [''])[0]
        
        return {
            'title': video_title,
            'download_url': download_url,
            'video_id': vid,
            'cover_url': cover_url,
            'author': video_detail.get('author', {}).get('nickname', 'Unknown'),
        }
    
    except requests.RequestException as e:
        raise Exception(f"网络请求失败：{e}")
    except Exception as e:
        raise Exception(f"解析失败：{e}")

def download_video(url, output_dir='./videos', timeout=300):
    """
    下载抖音视频
    
    Args:
        url: 抖音视频链接
        output_dir: 输出目录
        timeout: 下载超时（秒）
    
    Returns:
        str: 保存的文件路径
    """
    # 解析视频信息
    info = parse_douyin_url(url)
    
    # 创建输出目录
    output_path = Path(output_dir).expanduser().resolve()  # 支持 ~/videos 或绝对路径
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 清理文件名（移除特殊字符，限制长度）
    safe_title = re.sub(r'[^\w\u4e00-\u9fff\-_]', '_', info['title'])[:50]
    safe_author = re.sub(r'[^\w\u4e00-\u9fff]', '_', info.get('author', 'unknown'))[:20]
    filename = f"{safe_author}_{safe_title}_{info['video_id']}.mp4"
    video_path = output_path / filename
    
    # 检查是否已下载
    if video_path.exists():
        print(f"⚠ 文件已存在，跳过：{video_path}")
        return str(video_path)
    
    print(f"📥 开始下载:")
    print(f"  标题：{info['title']}")
    print(f"  作者：{info.get('author', 'Unknown')}")
    print(f"  地址：{info['download_url']}")
    print(f"  保存：{video_path}")
    
    try:
        # 下载视频
        session = requests.Session()
        session.headers.update(DOWNLOAD_HEADERS)
        
        resp = session.get(info['download_url'], stream=True, timeout=timeout)
        
        # 处理重定向
        if resp.status_code == 302:
            redirect_url = resp.headers['location']
            print(f"  ↪ 重定向到：{redirect_url}")
            resp = session.get(redirect_url, stream=True, timeout=timeout)
        
        resp.raise_for_status()
        
        # 获取文件大小
        total_size = int(resp.headers.get('content-length', 0))
        downloaded = 0
        
        # 写入文件
        with open(video_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # 显示进度
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r  进度：{percent:.1f}%", end='', flush=True)
        
        print(f"\n✓ 下载完成：{video_path}")
        print(f"  大小：{downloaded / 1024 / 1024:.2f} MB")
        
        return str(video_path)
    
    except Exception as e:
        # 下载失败则删除临时文件
        if video_path.exists():
            video_path.unlink()
        raise Exception(f"下载失败：{e}")

def main():
    if len(sys.argv) < 2:
        print("📺 抖音视频下载工具（无水印）")
        print()
        print("用法:")
        print("  python douyin_download.py <抖音视频链接> [输出目录]")
        print()
        print("示例:")
        print("  python douyin_download.py https://v.douyin.com/xxxxx")
        print("  python douyin_download.py https://v.douyin.com/xxxxx ./my_videos")
        print()
        sys.exit(1)
    
    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './videos'
    
    try:
        video_path = download_video(url, output_dir)
        print(f"\n✅ 成功保存到：{video_path}")
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
