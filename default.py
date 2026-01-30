#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kodi 注音輸入法 - 主程式入口
"""

import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

# 將 lib 加入路徑
ADDON = xbmcaddon.Addon()
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
sys.path.insert(0, ADDON_PATH)

from resources.lib.ui.keyboard_window import show_zhuyin_keyboard


def log(message: str, level: int = xbmc.LOGINFO):
    """記錄日誌"""
    xbmc.log(f"[script.input.zhuyin] {message}", level)


def parse_args() -> dict:
    """解析啟動參數"""
    args = {}
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                args[key] = value
            else:
                args[arg] = True
    
    return args


def main():
    """主函數"""
    log("注音輸入法啟動")
    
    args = parse_args()
    
    # 取得回調插件 ID（如果有）
    callback_addon = args.get('callback', None)
    initial_text = args.get('text', '')
    
    # 定義回調函數
    def on_input_complete(text):
        if text is None:
            log("輸入已取消")
            return
        
        log(f"輸入完成: {text}")
        
        if callback_addon:
            # 透過 JSON-RPC 或其他方式回傳結果
            # 這裡簡化處理，直接設定屬性
            xbmcgui.Window(10000).setProperty(
                f'zhuyin_input_result_{callback_addon}', 
                text
            )
        else:
            # 複製到剪貼簿（如果可用）
            try:
                import subprocess
                # LibreELEC 可能沒有 xclip，這裡做基本處理
                log(f"輸入結果: {text}")
            except:
                pass
    
    # 顯示鍵盤
    result = show_zhuyin_keyboard(
        callback=on_input_complete,
        initial_text=initial_text
    )
    
    log(f"注音輸入法結束，結果: {result}")


if __name__ == '__main__':
    main()
