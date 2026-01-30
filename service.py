#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kodi 注音輸入法 - 背景服務
監聽快捷鍵以啟動輸入法
"""

import xbmc
import xbmcaddon
import xbmcgui

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')


def log(message: str, level: int = xbmc.LOGINFO):
    """記錄日誌"""
    xbmc.log(f"[{ADDON_ID}] {message}", level)


class ZhuyinService(xbmc.Monitor):
    """注音輸入法背景服務"""
    
    def __init__(self):
        super().__init__()
        self.running = True
        log("注音輸入法服務啟動")
    
    def onSettingsChanged(self):
        """設定變更時"""
        log("設定已變更")
        # 重新載入設定
        ADDON.clearSettings()
    
    def onNotification(self, sender: str, method: str, data: str):
        """
        處理通知
        
        可以監聽自訂通知來啟動輸入法
        """
        if method == 'Other.ZhuyinInput':
            log("收到啟動輸入法通知")
            self._launch_keyboard()
    
    def _launch_keyboard(self):
        """啟動輸入法"""
        xbmc.executebuiltin(f'RunScript({ADDON_ID})')
    
    def run(self):
        """服務主迴圈"""
        # 服務保持運行
        while self.running and not self.abortRequested():
            # 監控原生鍵盤是否開啟
            # 如果原生鍵盤開啟，且我們的鍵盤未開啟，則啟動我們的鍵盤
            # 增加檢查：如果原生鍵盤標題是 "English Input"，則不啟動注音鍵盤 (避免無限迴圈)
            if xbmc.getCondVisibility('Window.IsActive(virtualkeyboard)') and \
               not xbmc.getCondVisibility('Window.IsActive(10147)'):
                
                # 取得原生鍵盤標題 (透過 InfoLabel)
                # 注意：Kodi API 沒有直接取得鍵盤標題的方法，但我們可以透過檢查是否是我們自己呼叫的來避免
                # 這裡使用一個簡單的延遲與屬性檢查機制
                
                # 檢查是否暫停監控 (由注音鍵盤設定)
                if xbmcgui.Window(10000).getProperty('zhuyin.pause_monitor') == 'true':
                    xbmc.sleep(500)
                    continue

                # 啟動注音輸入法 (Overlay 模式)
                xbmc.executebuiltin(f'RunScript({ADDON_ID}, mode=overlay)')
                
                # 等待一下避免重複啟動
                xbmc.sleep(1000)
            
            if self.waitForAbort(0.5):
                break
        
        log("注音輸入法服務結束")


def main():
    """服務入口"""
    service = ZhuyinService()
    service.run()


if __name__ == '__main__':
    main()
