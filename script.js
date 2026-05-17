const API_BASE =
  "https://test-1-5r5k.onrender.com";


// ====================================
// 校园资讯
// ====================================
async function loadNews() {

  const list =
    document.getElementById("news-list");

  if (!list) return;

  list.innerHTML = "加载中...";

  try {

    const response = await fetch(
      `${API_BASE}/api/news`
    );

    const data = await response.json();

    list.innerHTML = "";

    data.forEach(item => {

      list.innerHTML += `

        <div class="news-card">

          <h3>${item.title}</h3>

          <p>${item.summary}</p>

          <a
            href="${item.url}"
            target="_blank"
          >
            查看原文
          </a>

        </div>
      `;
    });

  } catch (e) {

    list.innerHTML =
      "校园资讯加载失败";
  }
}


// ====================================
// URL网页分析
// ====================================
async function analyzeUrl() {

  const url =
    document.getElementById("url-input").value;

  const result =
    document.getElementById("url-result");

  if (!url) return;

  result.innerHTML = "分析中...";

  try {

    const response = await fetch(
      `${API_BASE}/api/summarize`,
      {

        method: "POST",

        headers: {

          "Content-Type":
            "application/json"
        },

        body: JSON.stringify({
          url
        })
      }
    );

    const data = await response.json();

    if (data.error) {

      result.innerHTML =
        `错误：${data.error}`;

      return;
    }


    let html = `

      <h2>${data.title}</h2>

      <div class="summary-box">

        <h3>🧠 AI总结</h3>

        <p>${data.summary}</p>

      </div>
    `;


    // ====================================
    // 页面链接
    // ====================================
    if (
      data.links &&
      data.links.length > 0
    ) {

      html += `

        <div class="link-box">

        <h3>🔗 页面链接</h3>
      `;

      data.links.forEach(link => {

        html += `

          <p>

            <a
              href="${link.url}"
              target="_blank"
            >

              ${link.text}

            </a>

          </p>
        `;
      });

      html += `</div>`;
    }


    // ====================================
    // 页面附件
    // ====================================
    if (
      data.attachments &&
      data.attachments.length > 0
    ) {

      html += `

        <div class="attach-box">

        <h3>📎 页面附件</h3>
      `;

      data.attachments.forEach(file => {

        html += `

          <p>

            <a
              href="${file.url}"
              target="_blank"
            >

              📎 ${file.name}

            </a>

          </p>
        `;
      });

      html += `</div>`;
    }


    // ====================================
    // 页面图片
    // ====================================
    if (
      data.images &&
      data.images.length > 0
    ) {

      html += `

        <div class="image-box">

        <h3>🖼 页面图片</h3>

        <div class="image-grid">
      `;

      data.images.forEach(img => {

        html += `

          <img
            src="${img}"
            class="preview-image"
          >
        `;
      });

      html += `
        </div>
        </div>
      `;
    }

    result.innerHTML = html;

  } catch (e) {

    result.innerHTML =
      "分析失败";
  }
}


// ====================================
// AI聊天（多轮）
// ====================================
let messages = [

  {
    role: "system",
    content: "你是AI助手"
  }

];


async function sendMessage() {

  const input =
    document.getElementById("chat-input");

  const text = input.value;

  if (!text) return;

  const box =
    document.getElementById("chat-box");

  box.innerHTML += `

    <div class="user-msg">

      ${text}

    </div>
  `;

  input.value = "";

  messages.push({

    role: "user",

    content: text
  });

  try {

    const response = await fetch(
      `${API_BASE}/api/chat`,
      {

        method: "POST",

        headers: {

          "Content-Type":
            "application/json"
        },

        body: JSON.stringify({
          messages
        })
      }
    );

    const data = await response.json();

    messages.push({

      role: "assistant",

      content: data.reply
    });

    box.innerHTML += `

      <div class="ai-msg">

        ${data.reply}

      </div>
    `;

    box.scrollTop =
      box.scrollHeight;

  } catch (e) {

    box.innerHTML += `

      <div class="ai-msg">

        AI请求失败

      </div>
    `;
  }
}


// 初始化
loadNews();
