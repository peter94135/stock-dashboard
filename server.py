#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票題材儀表板 本機伺服器 / Yahoo Finance 代理
- 同時提供 HTML 與 /yf 代理端點
- 用你自己的網路 IP 完成 Yahoo cookie + crumb 握手，避開 CORS 與限流
用法： python3 server.py  （或直接雙擊「啟動儀表板.command」）
"""
import http.server, socketserver, urllib.request, urllib.parse, http.cookiejar
import os, sys, json, webbrowser, threading, ssl

# macOS 的 python.org Python 常缺系統憑證；優先用 certifi，否則退回不驗證（僅讀公開行情）
try:
    import certifi
    _ctx = ssl.create_default_context(cafile=certifi.where())
except Exception:
    try:
        _ctx = ssl.create_default_context()
        _ctx.check_hostname = False
        _ctx.verify_mode = ssl.CERT_NONE
    except Exception:
        _ctx = ssl._create_unverified_context()

PORT = 8765
HTML_FILE = "index.html"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

_cookiejar = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(_cookiejar),
    urllib.request.HTTPSHandler(context=_ctx))
_opener.addheaders = [("User-Agent", UA), ("Accept", "*/*")]
_crumb = None

def _get(url):
    return _opener.open(urllib.request.Request(url), timeout=15).read()

def handshake():
    """取得 Yahoo cookie 與 crumb（失敗不致命，chart 端點通常只需 cookie）。"""
    global _crumb
    for seed in ("https://finance.yahoo.com", "https://fc.yahoo.com"):
        try: _get(seed)
        except Exception: pass
    try:
        _crumb = _get("https://query2.finance.yahoo.com/v1/test/getcrumb").decode("utf-8").strip()
        if "Too Many" in _crumb or "<" in _crumb:
            _crumb = None
    except Exception:
        _crumb = None
    print("  crumb:", "OK" if _crumb else "（無，仍可抓行情）")

def yahoo_fetch(target):
    """抓 Yahoo URL，需要 crumb 的端點自動補上；遇限流重握手重試一次。"""
    def build(u):
        if _crumb and ("quoteSummary" in u or "/v7/finance/quote" in u) and "crumb=" not in u:
            sep = "&" if "?" in u else "?"
            u = u + sep + "crumb=" + urllib.parse.quote(_crumb)
        return u
    for attempt in range(2):
        try:
            raw = _get(build(target))
            txt = raw.decode("utf-8", "replace")
            if "Too Many Requests" in txt or "Invalid Cookie" in txt or "Unauthorized" in txt:
                raise RuntimeError("blocked")
            return raw
        except Exception:
            if attempt == 0:
                handshake()
            else:
                raise

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass  # 安靜

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/yf":
            qs = urllib.parse.parse_qs(parsed.query)
            target = (qs.get("url") or [""])[0]
            if not target.startswith("https://query"):
                self.send_error(400, "bad url"); return
            try:
                raw = yahoo_fetch(target)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(raw)
            except Exception as e:
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        if parsed.path in ("/", ""):
            self.path = "/" + urllib.parse.quote(HTML_FILE)
        return super().do_GET()

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists(HTML_FILE):
        print("找不到", HTML_FILE); sys.exit(1)
    print("正在向 Yahoo 握手取得授權…")
    handshake()
    url = f"http://localhost:{PORT}/"
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"\n  ✅ 儀表板啟動： {url}")
        print("  （關閉此視窗即停止伺服器）\n")
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止。")

if __name__ == "__main__":
    main()
