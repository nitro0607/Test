async function search() {
  const input = document.getElementById("input").value;
  const resultDiv = document.getElementById("result");

  if (!input) {
    resultDiv.innerText = "请输入问题";
    return;
  }

  resultDiv.innerText = "🤖 正在思考中...";

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
    resultDiv.innerText = "❌ 请求失败，请检查网络";
  }
}
