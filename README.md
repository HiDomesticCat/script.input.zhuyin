# Kodi 注音輸入法 (Zhuyin Input Method)

專為 Kodi 媒體中心設計的繁體中文注音輸入法插件，針對遙控器操作優化。

![版本](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Kodi](https://img.shields.io/badge/Kodi-20%2B-green.svg)
![授權](https://img.shields.io/badge/license-MIT-yellow.svg)

## 功能特色

- 🎮 **遙控器優化** - 專為電視遙控器和 CEC 控制設計
- 📝 **注音輸入** - 支援標準（大千）鍵盤佈局
- 🔤 **智能候選** - 詞組預測與詞頻排序
- 📚 **學習功能** - 記錄用戶選字習慣，支援唯讀系統 (LibreELEC)
- 🔢 **快速選字** - 數字鍵 1-9 快速選擇候選詞
- ⚡ **符號輸入** - 全形/半形標點符號
- 🖥️ **原生介面** - 整合 Kodi 原生 UI (WindowXMLDialog)，支援各種佈景主題

## 安裝方式

### 方法一：直接安裝

1. 下載 `script.input.zhuyin.zip`
2. 在 Kodi 中進入 **設定** → **附加元件** → **從 zip 檔案安裝**
3. 選擇下載的 zip 檔案
4. 等待安裝完成

### 方法二：手動安裝

1. 解壓縮 `script.input.zhuyin.zip`
2. 將 `script.input.zhuyin` 資料夾複製到：
   - **LibreELEC/CoreELEC**: `/storage/.kodi/addons/`
   - **Windows**: `%APPDATA%\Kodi\addons\`
   - **Linux**: `~/.kodi/addons/`
   - **macOS**: `~/Library/Application Support/Kodi/addons/`
3. 重新啟動 Kodi

## 使用方式

### 啟動輸入法

在 Kodi 中執行：
```
RunScript(script.input.zhuyin)
```

或透過其他插件呼叫：
```python
xbmc.executebuiltin('RunScript(script.input.zhuyin)')
```

### 遙控器操作

| 按鍵 | 功能 |
|------|------|
| **方向鍵** | 移動鍵盤焦點 |
| **確認鍵** | 輸入選中的注音符號 |
| **數字鍵 1-9** | 快速選擇候選詞 |
| **返回鍵** | 刪除 / 取消 |
| **長按確認** | 送出文字 |

### 輸入流程

1. 使用方向鍵選擇注音符號
2. 按確認鍵輸入符號
3. 輸入聲調（或按空格選擇一聲）完成音節
4. 使用數字鍵選擇候選詞
5. 按「確認送出」完成輸入

## 鍵盤佈局

```
┌─────────────────────────────────────────────────────┐
│  輸入狀態列：ㄊㄞˊ ㄨㄢ                              │
├─────────────────────────────────────────────────────┤
│  候選詞：1.台灣 2.太晚 3.抬碗 4.臺灣 5.颱彎 ...     │
├─────────────────────────────────────────────────────┤
│    ㄅ   ㄉ   ˇ   ˋ   ㄓ   ˊ   ˙   ㄚ   ㄞ   ㄢ    │
│    ㄆ   ㄊ   ㄍ   ㄐ   ㄔ   ㄗ   ㄧ   ㄛ   ㄟ   ㄣ    │
│    ㄇ   ㄋ   ㄎ   ㄑ   ㄕ   ㄘ   ㄨ   ㄜ   ㄠ   ㄤ    │
│    ㄈ   ㄌ   ㄏ   ㄒ   ㄖ   ㄙ   ㄩ   ㄝ   ㄡ   ㄥ    │
│    [符號]  [空格]  [刪除]  [ㄦ]        [確認送出]    │
└─────────────────────────────────────────────────────┘
```

## 設定選項

進入 **設定** → **附加元件** → **script.input.zhuyin** → **設定**

- **候選詞數量**: 5 / 7 / 9
- **啟用學習功能**: 記錄選字習慣
- **自動送出**: 單一候選時自動送出
- **全形符號**: 使用全形標點符號
- **模糊聲調**: 允許模糊聲調匹配

## 詞庫資訊

內建詞庫包含：
- 約 860+ 常用單字
- 約 100+ 常用詞組
- 支援用戶自訂詞庫

## 開發者整合

### 在其他插件中呼叫

```python
import xbmc
import xbmcgui

# 啟動輸入法
xbmc.executebuiltin('RunScript(script.input.zhuyin,callback=your.addon.id)')

# 取得輸入結果
result = xbmcgui.Window(10000).getProperty('zhuyin_input_result_your.addon.id')
```

### 帶初始文字

```python
xbmc.executebuiltin('RunScript(script.input.zhuyin,text=初始文字)')
```

## 檔案結構

```
script.input.zhuyin/
├── addon.xml              # 插件定義
├── default.py             # 主程式入口
├── service.py             # 背景服務
├── resources/
│   ├── settings.xml       # 設定介面
│   ├── data/
│   │   ├── phrases.db     # 詞庫資料庫
│   │   └── symbols.json   # 符號表
│   ├── language/          # 語言檔
│   ├── lib/               # Python 模組
│   │   ├── engine/        # 輸入法引擎
│   │   ├── ui/            # 使用者介面
│   │   └── utils/         # 工具函數
│   └── skins/             # UI 佈局
```

## 系統需求

- Kodi 21 (Omega) 或更新版本
- Python 3.11+

## 已測試平台

- ✅ LibreELEC 12.2.1 (Linux Kernel 6.12.56)
- ✅ CoreELEC
- ✅ Windows 10/11
- ✅ Ubuntu / Debian
- ✅ macOS

## 技術細節

### LibreELEC / Read-Only 系統相容性
本插件已針對唯讀檔案系統 (Read-Only Filesystem) 進行優化：
- **系統詞庫**: 預設為唯讀模式，避免在 `/usr/share/kodi/addons` 等唯讀路徑下寫入。
- **用戶資料**: 所有學習記錄與自訂詞組皆儲存於 `/storage/.kodi/userdata/addon_data/` (profile 目錄)。
- **SQLite 優化**: 使用 `mode=ro` 與 `uri=True` 確保在唯讀媒體上正確開啟資料庫。

## 常見問題

### Q: 找不到某些字？
A: 內建詞庫為精簡版本，可透過設定匯入更完整的詞庫。

### Q: 遙控器按鍵沒反應？
A: 確認 CEC 功能已啟用，某些電視遙控器可能不支援所有按鍵。

### Q: 如何清除學習記錄？
A: 進入插件設定 → 進階 → 清除學習歷史

## 更新日誌

### v1.0.0
- 首次發布
- 基本注音輸入功能
- 詞組預測
- 用戶學習功能

## 授權

本專案採用 MIT 授權條款。詳見 [LICENSE](LICENSE.txt)。

## 致謝

- [Kodi](https://kodi.tv/) - 開源媒體中心
- [萌典](https://github.com/g0v/moedict-data) - 開源中文詞典

## 貢獻

歡迎提交 Issue 和 Pull Request！

---

**Made with ❤️ for the Traditional Chinese Kodi community**
