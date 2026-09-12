document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("loginError");
  errorEl.classList.add("hidden");

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  const res = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (res.ok) {
    location.href = "/";
    return;
  }

  let msg = "로그인에 실패했습니다";
  try {
    const j = await res.json();
    if (j.error) msg = j.error;
  } catch (e2) {}
  errorEl.textContent = msg;
  errorEl.classList.remove("hidden");
});
