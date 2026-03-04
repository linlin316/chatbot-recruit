// 主要UI要素を取得する
const fab = document.getElementById("chatFab");
const widget = document.getElementById("chatWidget");
const closeBtn = document.getElementById("chatClose");
const body = document.getElementById("chatBody");
const form = document.getElementById("chatForm");
const input = document.getElementById("chatInput");
const subArea = document.getElementById("quick-sub");


// チャット画面にメッセージバブルを追加する
function addMsg(text, who) {
    const wrap = document.createElement("div");
    wrap.className = `msg ${who}`;
    wrap.innerHTML = `<div class="bubble"></div>`; 

    const bubble = wrap.querySelector(".bubble");
    body.appendChild(wrap);

    // 常に最下部へ
    body.scrollTop = body.scrollHeight;

    // botだけ1文字ずつ表示する
    if (who === "bot") {
        typeWriter(text, bubble, 25);
    } else {
        bubble.textContent = text;
    }
}

// テキストを1文字ずつ表示する
function typeWriter(text, el, speed = 18) {
  el.textContent = "";
  let i = 0;

  function tick() {
    if (i < text.length) {
      el.textContent += text.charAt(i);
      i++;
      el.scrollIntoView({ block: "end" }); // 追従スクロール
      setTimeout(tick, speed);
    }
  }

  tick();
}


// チャットウィジェットの表示／非表示を切り替える
function toggle(open) {
    widget.style.display = open ? "flex" : "none";
    if (open) input.focus();
    }


// チャットを開く/閉める
fab.addEventListener("click", () => toggle(true));
closeBtn.addEventListener("click", () => toggle(false));

// 送信中フラグ（二重送信防止）
let isSending = false;


// サーバーの /chat API に問い合わせてボット応答を取得する
// HTTPエラー・ネットワークエラー時はユーザー向けメッセージを返す
async function sendToServer(message) {
    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message})
        });

        if (!res.ok) {
            return "エラーが発生しました。時間をおいて再度お試しください。";
        }

        const data = await res.json();
        return data.reply || "（返答が取得できませんでした）";
    } catch (e) {
        // ネットワーク切断・タイムアウトなどの通信エラー
        return "通信エラーが発生しました。接続を確認してください。";
    }
}


// クイック返信ボタンの定義
// label: ボタンの表示名
// q: サーバーに送信する質問文
const SUB_OPTIONS = {
    work: [
    { label: "勤務地", q: "勤務地について" },
    { label: "勤務時間", q: "勤務時間について" },
    { label: "仕事内容", q: "仕事内容について" },
    { label: "リモート", q: "リモート勤務について" },
    { label: "残業", q: "残業について" },
    ],

    benefits: [
    { label: "福利厚生", q: "福利厚生について" },
    { label: "健康保険", q: "健康保険について" },
    { label: "休日・休暇", q: "休み（休日・休暇）について" },
    { label: "手当", q: "各種手当について" },
    { label: "給与", q: "給与・待遇について" },
    ],

    company: [
    { label: "応募方法", q: "応募方法について" },
    { label: "選考フロー", q: "選考フローについて" },
    { label: "募集職種", q: "募集職種について" },
    { label: "事業内容", q: "事業内容について" },
    { label: "会社概要", q: "会社概要について" },
    ]
};


// 大分類ボタン押下 → 小分類ボタン生成
document.querySelectorAll(".main-btn").forEach(btn => {
    btn.addEventListener("click", () => {
    const cat = btn.dataset.cat;
    subArea.innerHTML = "";

    SUB_OPTIONS[cat].forEach(item => {
        const b = document.createElement("button");
        b.className = "quick-btn";
        b.dataset.q = item.q;
        b.textContent = item.label;
        subArea.appendChild(b);
        });
    });
});


// 小分類ボタンクリック時：質問送信 → ボット応答表示
document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".quick-btn");
    if (!btn) return;

    const q = btn.dataset.q || "";
    if (!q || isSending) return;

    isSending = true;
    addMsg(q, "user");
    const reply = await sendToServer(q);
    addMsg(reply, "bot");
    isSending = false;
});


// 入力送信処理
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text || isSending) return;

    isSending = true;
    input.value = "";
    input.disabled = true;

    addMsg(text, "user");
    const reply = await sendToServer(text);
    addMsg(reply, "bot");

    input.disabled = false;
    input.focus();
    isSending = false;
});