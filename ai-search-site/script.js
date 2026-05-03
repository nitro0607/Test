async function search() {
  const input = document.getElementById("input").value;
  const resultDiv = document.getElementById("result");

  resultDiv.innerText = "正在思考中...";

  const res = await fetch("/api/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ query: input })
  });

  const data = await res.json();
  resultDiv.innerText = data.result;
}