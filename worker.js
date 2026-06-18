/**
 * Cloudflare Worker — Yahoo Finance 代理（含 cookie + crumb 握手）
 * 部署後線上版即可完整顯示 P/E、市值，股價也更快更穩。
 *
 * 用法：GET https://<你的worker>.workers.dev/?url=<encodeURIComponent(yahoo_api_url)>
 * 免費方案每日 10 萬次請求，綽綽有餘。
 */

const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
           "(KHTML, like Gecko) Chrome/120.0 Safari/537.36";

let cookie = null;   // 在同一個 isolate 內快取，跨請求重複使用
let crumb = null;

async function handshake() {
  cookie = null; crumb = null;
  // 1) 取 cookie
  for (const seed of ["https://fc.yahoo.com/", "https://finance.yahoo.com/"]) {
    try {
      const r = await fetch(seed, { headers: { "User-Agent": UA }, redirect: "manual" });
      const sc = r.headers.get("set-cookie");
      if (sc) { cookie = sc.split(";")[0]; break; }
    } catch (e) {}
  }
  // 2) 取 crumb
  try {
    const r = await fetch("https://query2.finance.yahoo.com/v1/test/getcrumb",
      { headers: { "User-Agent": UA, "Cookie": cookie || "" } });
    const c = (await r.text()).trim();
    crumb = (c && !/\s/.test(c) && !c.includes("<")) ? c : null;
  } catch (e) { crumb = null; }
}

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,OPTIONS",
  "Access-Control-Allow-Headers": "*",
};

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });

    const target = new URL(request.url).searchParams.get("url");
    if (!target || !target.startsWith("https://query")) {
      return json({ error: "bad url" }, 400);
    }

    const needsCrumb = (u) =>
      (u.includes("quoteSummary") || u.includes("/v7/finance/quote")) && !u.includes("crumb=");

    async function call() {
      let u = target;
      if (crumb && needsCrumb(u)) u += (u.includes("?") ? "&" : "?") + "crumb=" + encodeURIComponent(crumb);
      return fetch(u, { headers: { "User-Agent": UA, "Cookie": cookie || "", "Accept": "*/*" } });
    }

    try {
      if (!cookie || !crumb) await handshake();
      let resp = await call();
      let body = await resp.text();
      if (resp.status === 401 || resp.status === 429 ||
          body.includes("Too Many Requests") || body.includes("Invalid Cookie") || body.includes("Unauthorized")) {
        await handshake();              // 重握手再試一次
        resp = await call();
        body = await resp.text();
      }
      return new Response(body, {
        status: resp.status,
        headers: { ...CORS, "Content-Type": "application/json; charset=utf-8" },
      });
    } catch (e) {
      return json({ error: String(e) }, 502);
    }
  },
};

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status, headers: { ...CORS, "Content-Type": "application/json" },
  });
}
