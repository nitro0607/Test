async function search() {
  const input = document.getElementById("input").value.trim();
  const resultDiv = document.getElementById("result");

  if (!input) {
    resultDiv.innerText = "请输入内容";
    return;
  }

  // 判断是否是URL
  const isURL = input.startsWith("http://") || input.startsWith("https://");

  if (isURL) {
    resultDiv.innerText = "🌐 正在抓取网页并总结...";

    try {
      const res = await fetch("https://test-1-5r5k.onrender.com/api/summarize"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ url: input })
      });

      const data = await res.json();

      if (data.error) {
        resultDiv.innerText = "❌ 错误：" + data.error;
      } else {
        resultDiv.innerText =
          "📄 标题：\n" + data.title + "\n\n🧠 摘要：\n" + data.summary;
      }
    } catch (err) {
      resultDiv.innerText = "❌ 网页抓取失败";
    }

  } else {
    // 原AI功能
    resultDiv.innerText = "🤖 AI思考中...";

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ query: input })
      });

      const data = await res.json();
      resultDiv.innerText = data.result;

    } catch (err) {
      resultDiv.innerText = "❌ AI请求失败";
    }
  }
}
