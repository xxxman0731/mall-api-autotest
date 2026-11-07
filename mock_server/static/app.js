// Mall 商城前端交互:商品浏览 / 登录注册 / 下单 / 我的订单
const state = {
  token: localStorage.getItem("mall_token") || "",
  username: localStorage.getItem("mall_username") || "",
  authMode: "login",
  view: "products",
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// 商品封面配色与图标(按商品 id 循环取用)
const gradients = [
  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
  "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
  "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
  "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
  "linear-gradient(135deg, #30cfd0 0%, #330867 100%)",
];
const emojis = ["📱", "⌚", "🖱️", "⌨️", "🖥️", "🛒"];

function coverOf(product) {
  const i = (product.id || 0) % gradients.length;
  return { gradient: gradients[i], emoji: emojis[i] };
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = "Bearer " + state.token;
  const resp = await fetch(path, { ...options, headers });
  let body = null;
  try { body = await resp.json(); } catch (e) { body = null; }
  if (resp.status === 401 && path !== "/api/login") {
    openAuth();
    throw new Error(body ? body.msg : "请先登录");
  }
  if (!resp.ok || !body || body.code !== 0) {
    throw new Error(body ? body.msg : "请求失败(" + resp.status + ")");
  }
  return body.data;
}

function toast(msg, type = "success") {
  const el = $("#toast");
  el.textContent = msg;
  el.className = "toast show " + type;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { el.className = "toast hidden"; }, 2600);
}

function money(n) { return "¥" + Number(n).toFixed(2); }

// ===== 商品 =====
async function loadProducts() {
  const grid = $("#productGrid");
  grid.innerHTML = '<div class="loading"><span class="spinner"></span>加载中…</div>';
  try {
    const products = await api("/api/products");
    if (!products.length) {
      grid.innerHTML = '<div class="empty">暂无商品</div>';
      return;
    }
    grid.innerHTML = "";
    products.forEach((p) => grid.appendChild(renderCard(p)));
  } catch (err) {
    grid.innerHTML = '<div class="empty">加载失败:' + esc(err.message) + "<br>请确认后端服务已启动</div>";
  }
}

function renderCard(p) {
  const cover = coverOf(p);
  const card = document.createElement("article");
  card.className = "card";
  card.innerHTML =
    '<div class="card-cover" style="background:' + cover.gradient + '"><span>' + cover.emoji + "</span></div>" +
    '<div class="card-body">' +
    '  <div class="card-title">' + esc(p.name) + "</div>" +
    '  <div class="card-price">' + money(p.price) + "</div>" +
    '  <div class="card-meta"><span class="stock ' + (p.stock <= 0 ? "stock-empty" : "") + '">库存 ' + p.stock + "</span></div>" +
    '  <div class="buy-row">' +
    '    <div class="qty">' +
    '      <button class="qty-btn" data-act="minus">−</button>' +
    '      <span class="qty-num">1</span>' +
    '      <button class="qty-btn" data-act="plus">+</button>' +
    "    </div>" +
    '    <button class="btn btn-primary buy-btn"' + (p.stock <= 0 ? " disabled" : "") + ">立即购买</button>" +
    "  </div>" +
    "</div>";
  const num = card.querySelector(".qty-num");
  let qty = 1;
  card.querySelector('[data-act="minus"]').addEventListener("click", () => {
    qty = Math.max(1, qty - 1);
    num.textContent = qty;
  });
  card.querySelector('[data-act="plus"]').addEventListener("click", () => {
    qty = Math.min(99, p.stock, qty + 1);
    num.textContent = qty;
  });
  card.querySelector(".buy-btn").addEventListener("click", () => buy(p, qty));
  return card;
}

async function buy(p, qty) {
  if (!state.token) { openAuth(); return; }
  try {
    const order = await api("/api/orders", {
      method: "POST",
      body: JSON.stringify({ product_id: p.id, quantity: qty }),
    });
    toast("下单成功,订单号 " + order.order_no);
    await loadProducts();
    if (state.view === "orders") await loadOrders();
  } catch (err) {
    toast(err.message, "error");
  }
}

// ===== 订单 =====
async function loadOrders() {
  const list = $("#orderList");
  if (!state.token) {
    list.innerHTML = '<div class="empty">登录后查看订单</div>';
    return;
  }
  list.innerHTML = '<div class="loading"><span class="spinner"></span>加载中…</div>';
  try {
    const orders = await api("/api/orders");
    if (!orders.length) {
      list.innerHTML = '<div class="empty">还没有订单,去挑点好物吧 🛒</div>';
      return;
    }
    list.innerHTML = "";
    orders.forEach((o) => {
      const item = document.createElement("div");
      item.className = "order-card";
      item.innerHTML =
        '<div class="order-head">' +
        '  <span class="order-no">' + esc(o.order_no) + "</span>" +
        '  <span class="order-time">' + esc(o.created_at) + "</span>" +
        "</div>" +
        '<div class="order-body">' +
        '  <div class="order-cover">' + coverOf({ id: o.product_id }).emoji + "</div>" +
        '  <div class="order-info">' +
        '    <div class="order-name">' + esc(o.product_name) + "</div>" +
        '    <div class="order-sub">数量 ×' + o.quantity + "</div>" +
        "  </div>" +
        '  <div class="order-total">' + money(o.total_price) + "</div>" +
        "</div>";
      list.appendChild(item);
    });
  } catch (err) {
    list.innerHTML = '<div class="empty">加载失败:' + esc(err.message) + "</div>";
  }
}

// ===== 视图切换 =====
function switchView(view) {
  state.view = view;
  $$(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  $$(".view").forEach((v) => v.classList.toggle("active", v.id === "view-" + view));
  if (view === "orders") loadOrders();
  if (view === "products") loadProducts();
}

// ===== 登录 / 注册 =====
function openAuth() { $("#authModal").classList.remove("hidden"); }
function closeAuth() { $("#authModal").classList.add("hidden"); }

function setAuthMode(mode) {
  state.authMode = mode;
  $("#modalTitle").textContent = mode === "login" ? "欢迎回来" : "创建账号";
  $("#submitBtn").textContent = mode === "login" ? "登 录" : "注 册";
  $("#tabLogin").classList.toggle("active", mode === "login");
  $("#tabRegister").classList.toggle("active", mode === "register");
  $("#phoneField").classList.toggle("hidden", mode !== "register");
}

async function submitAuth(e) {
  if (e && e.preventDefault) e.preventDefault();
  const username = $("#username").value.trim();
  const password = $("#password").value;
  if (!username || !password) {
    toast("请填写用户名和密码", "error");
    return;
  }
  const isRegister = state.authMode === "register";
  const payload = { username, password };
  if (isRegister) {
    const phone = $("#phone").value.trim();
    if (phone) payload.phone = phone;
  }
  try {
    const resp = await fetch(isRegister ? "/api/register" : "/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await resp.json();
    if (!resp.ok || body.code !== 0) {
      toast(body.msg || "操作失败", "error");
      return;
    }
    if (isRegister) {
      toast("注册成功,请登录");
      setAuthMode("login");
      $("#password").value = "";
      return;
    }
    state.token = body.data.token;
    state.username = body.data.username;
    localStorage.setItem("mall_token", state.token);
    localStorage.setItem("mall_username", state.username);
    updateUserUI();
    closeAuth();
    toast("登录成功,欢迎 " + state.username);
    if (state.view === "orders") loadOrders();
  } catch (err) {
    toast("请求失败,请确认后端服务已启动", "error");
  }
}

function updateUserUI() {
  const logged = !!state.token;
  $("#userLabel").textContent = logged ? state.username : "";
  $("#userLabel").classList.toggle("hidden", !logged);
  $("#loginBtn").classList.toggle("hidden", logged);
  $("#logoutBtn").classList.toggle("hidden", !logged);
}

function logout() {
  state.token = "";
  state.username = "";
  localStorage.removeItem("mall_token");
  localStorage.removeItem("mall_username");
  updateUserUI();
  toast("已退出登录");
  if (state.view === "orders") loadOrders();
}

// ===== 事件绑定 =====
$$(".nav-btn").forEach((b) => b.addEventListener("click", () => switchView(b.dataset.view)));
$("#loginBtn").addEventListener("click", openAuth);
$("#logoutBtn").addEventListener("click", logout);
$("#modalClose").addEventListener("click", closeAuth);
$("#tabLogin").addEventListener("click", () => setAuthMode("login"));
$("#tabRegister").addEventListener("click", () => setAuthMode("register"));
$("#authForm").addEventListener("submit", submitAuth);
$("#authModal").addEventListener("click", (e) => {
  if (e.target.id === "authModal") closeAuth();
});
$("#password").addEventListener("keydown", (e) => {
  if (e.key === "Enter") submitAuth(e);
});

// ===== 初始化 =====
updateUserUI();
setAuthMode("login");
switchView("products");
