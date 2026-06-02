# 抖音视频下载 Skill

> 无水印下载抖音视频，支持单个视频链接快速下载

## 快速开始

### 1. 安装依赖

```bash
cd ~/.openclaw/plugin-skills/douyin-downloader
pip install -r requirements.txt
```

### 2. 使用方式

#### 命令行使用

```bash
# 下载单个视频到默认目录（./videos）
python douyin_download.py https://v.douyin.com/xxxxx

# 指定输出目录
python douyin_download.py https://v.douyin.com/xxxxx ~/Downloads/douyin
```

#### OpenClaw 中调用

```bash
# 在 OpenClaw exec 中调用
exec command="python ~/.openclaw/plugin-skills/douyin-downloader/douyin_download.py <视频链接>"
```

#### Python 代码调用

```python
from douyin_download import download_video

# 下载视频
video_path = download_video(
    url='https://v.douyin.com/xxxxx',
    output_dir='./videos'
)
print(f"下载完成：{video_path}")
```

## 功能特性

- ✅ 无水印下载
- ✅ 自动解析短链接（v.douyin.com）
- ✅ 提取视频标题和作者信息
- ✅ 自动创建输出目录
- ✅ 下载进度显示
- ✅ 跳过已下载文件
- ✅ 错误处理和重试机制

## 输出示例

```
📥 开始下载:
  标题：这是一个很棒的视频
  作者：某位创作者
  地址：http://www.iesdouyin.com/aweme/v1/play/...
  保存：/home/user/videos/某位创作者_这是一个很棒的视频_12345678.mp4
  进度：100.0%

✓ 下载完成：/home/user/videos/某位创作者_这是一个很棒的视频_12345678.mp4
  大小：15.23 MB

✅ 成功保存到：/home/user/videos/某位创作者_这是一个很棒的视频_12345678.mp4
```

## 注意事项

1. **接口稳定性**: 抖音接口可能随时变化，如下载失败请检查项目更新
2. **网络连接**: 需要能访问抖音服务器，国内可能需要代理
3. **版权**: 仅用于学习研究，请勿商用或侵犯版权
4. **频率限制**: 批量下载时建议添加延迟，避免触发反爬

## 故障排查

### 问题：解析失败，无法提取视频信息

**原因**: 抖音更新了页面结构或接口参数

**解决**:
1. 检查 GitHub 项目是否有更新
2. 尝试使用其他视频链接测试
3. 查看抖音网页版是否能正常播放

### 问题：下载超时或失败

**原因**: 网络连接问题或服务器限制

**解决**:
1. 检查网络连接
2. 配置代理（参考 FoxyProxy `127.0.0.1:38457`）
3. 增加超时时间：修改 `timeout` 参数

### 问题：文件名乱码

**原因**: 系统编码问题

**解决**:
```bash
export PYTHONIOENCODING=utf-8
python douyin_download.py ...
```

## 技术实现

核心流程：

1. **链接解析**: 处理短链接跳转，提取视频 ID
2. **页面抓取**: 请求视频详情页，提取 `window._ROUTER_DATA`
3. **JSON 解析**: 从页面数据中提取视频信息
4. **地址构造**: 生成无水印播放地址
5. **视频下载**: 流式下载到本地

详细实现参考 `SKILL.md` 文档。

## 参考项目

- [videodl](https://github.com/CharlesPikachu/videodl) - 2163⭐
- [douyin_downloader](https://github.com/renyijiu/douyin_downloader) - 483⭐

## 许可证

仅供学习研究使用，请勿用于商业目的。
