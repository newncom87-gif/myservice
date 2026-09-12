// 성경말씀 PPT 생성기 - 프론트엔드 (바닐라 JS, 단일 페이지)

const state = {
  books: [],
  blocks: [],
  defaultGroupSize: 2,
  overrides: [],
  background: { defaultId: "navy-fade" },
  slideBackgrounds: {},
  theme: {
    cover: {
      title: { text: "성경말씀", xPct: 0.10, yPct: 0.08, wPct: 0.80, hPct: 0.16, fontSize: 54, color: "#FFFFFF", bold: true, align: "center", fontFamily: "맑은 고딕" },
      verseRef: { xPct: 0.08, yPct: 0.34, wPct: 0.84, hPct: 0.26, fontSize: 26, color: "#F2E7C9", bold: false, align: "center", fontFamily: "맑은 고딕" },
      presenter: { text: "", xPct: 0.55, yPct: 0.84, wPct: 0.35, hPct: 0.09, fontSize: 20, color: "#DDDDDD", bold: false, align: "right", fontFamily: "맑은 고딕", show: true },
      overlay: { enabled: true, shape: "rect", color: "#000000", opacity: 0.45, xPct: 0.05, yPct: 0.05, wPct: 0.90, hPct: 0.90 },
    },
    body: {
      refTitle: { xPct: 0.06, yPct: 0.06, wPct: 0.70, hPct: 0.14, fontSize: 34, color: "#F2A93B", bold: true, align: "left", fontFamily: "맑은 고딕", show: true },
      verseText: { xPct: 0.06, yPct: 0.24, wPct: 0.88, hPct: 0.68, fontSize: 26, color: "#FFFFFF", numberColor: "#F2A93B", numberBold: true, bold: false, align: "left", fontFamily: "맑은 고딕", verseSpacing: 10 },
      overlay: { enabled: true, shape: "rect", color: "#000000", opacity: 0.50, xPct: 0.03, yPct: 0.03, wPct: 0.94, hPct: 0.94 },
    },
  },
  defaultBackgrounds: [],
  userBackgrounds: [],
  themesList: [],
  projectsList: [],
  fonts: [],
  manualBreaks: {}, // verseKey -> 사용자가 직접 줄바꿈(\n)을 넣은 절 본문 텍스트
  composed: { blockRefs: [], slides: [] },
  bgPickerTarget: null, // "global" | slide index(1-based body) | 0(cover)
};

const TITLE_PRESETS = ["성경봉독", "오늘의 성경", "성경말씀"];

// ---------- 유틸 ----------
async function api(path, opts) {
  const res = await fetch(path, opts);
  if (res.status === 401) {
    location.href = "login";
    throw new Error("로그인이 필요합니다");
  }
  if (!res.ok) {
    let msg = res.statusText;
    try { const j = await res.json(); if (j.error) msg = j.error; } catch (e) {}
    throw new Error(msg);
  }
  return res;
}
async function apiJson(path, opts) {
  const res = await api(path, opts);
  return res.json();
}
function el(tag, attrs = {}, children = []) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k === "text") e.textContent = v;
    else if (k.startsWith("on") && typeof v === "function") e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const c of [].concat(children)) if (c) e.appendChild(c);
  return e;
}
function hexToRgba(hex, opacity) {
  hex = (hex || "#000000").replace("#", "");
  const r = parseInt(hex.substring(0, 2), 16) || 0;
  const g = parseInt(hex.substring(2, 4), 16) || 0;
  const b = parseInt(hex.substring(4, 6), 16) || 0;
  return `rgba(${r},${g},${b},${opacity})`;
}
function formatRef(bookName, sc, sv, ec, ev) {
  if (ec === sc) return ev === sv ? `${bookName} ${sc}:${sv}` : `${bookName} ${sc}:${sv}~${ev}`;
  return `${bookName} ${sc}:${sv}~${ec}:${ev}`;
}
function bgUrl(ref) {
  if (!ref) return "";
  if (ref.defaultId) {
    const item = state.defaultBackgrounds.find((b) => b.id === ref.defaultId);
    return item ? `static/backgrounds/default/${item.file}` : "";
  }
  if (ref.uploadId) return `user-bg/${ref.uploadId}`;
  return "";
}

// ---------- 초기화 ----------
async function init() {
  state.books = await apiJson("api/books");
  const bgData = await apiJson("api/backgrounds");
  state.defaultBackgrounds = bgData.default;
  state.userBackgrounds = bgData.user;
  state.themesList = await apiJson("api/themes");
  state.projectsList = await apiJson("api/projects");
  state.fonts = await apiJson("api/fonts");

  populateBookSelect();
  await populateChaptersForBook();

  document.getElementById("bookSelect").addEventListener("change", populateChaptersForBook);
  document.getElementById("addBlockBtn").addEventListener("click", onAddBlock);
  document.getElementById("defaultGroupSize").addEventListener("change", (e) => {
    state.defaultGroupSize = parseInt(e.target.value) || 1;
    recompute();
  });
  document.getElementById("uploadInput").addEventListener("change", onUploadBackground);
  document.getElementById("saveThemeBtn").addEventListener("click", onSaveTheme);
  document.getElementById("themeSelect").addEventListener("change", onLoadTheme);
  document.getElementById("saveProjectBtn").addEventListener("click", onSaveProject);
  document.getElementById("projectSelect").addEventListener("change", onLoadProject);
  document.getElementById("newProjectBtn").addEventListener("click", onNewProject);
  document.getElementById("bgPickerClose").addEventListener("click", closeBgPicker);
  document.getElementById("generateBtn").addEventListener("click", onGenerate);
  document.getElementById("generateBtnBottom").addEventListener("click", onGenerate);
  document.getElementById("logoutBtn").addEventListener("click", async () => {
    await api("api/logout", { method: "POST" });
    location.href = "login";
  });
  document.getElementById("coverUndoBtn").addEventListener("click", undoTheme);
  document.getElementById("coverRedoBtn").addEventListener("click", redoTheme);
  document.getElementById("bodyUndoBtn").addEventListener("click", undoTheme);
  document.getElementById("bodyRedoBtn").addEventListener("click", redoTheme);
  document.addEventListener("keydown", (e) => {
    if (!(e.metaKey || e.ctrlKey)) return;
    const key = e.key.toLowerCase();
    const isUndo = key === "z" && !e.shiftKey;
    const isRedo = (key === "z" && e.shiftKey) || key === "y";
    if (!isUndo && !isRedo) return;
    if (e.target && e.target.isContentEditable) return; // 절 본문 줄바꿈 편집 중엔 브라우저 기본 실행취소 유지
    e.preventDefault();
    if (isUndo) undoTheme(); else redoTheme();
  });
  setupTabs();

  renderGlobalBgGallery();
  renderThemeSelect();
  renderProjectSelect();
  renderCoverEditor();
  renderBodyEditor();
  renderCoverControls();
  renderBodyControls();
  renderBlockList();
  await recompute();
  resetHistory();

  window.addEventListener("resize", debounce(() => rescaleTextBoxes(document.body), 150));
}

// ---------- 좌측 설정 탭(1~5) 전환 ----------
function setupTabs() {
  const tabBar = document.getElementById("tabBar");
  const buttons = [...tabBar.querySelectorAll(".tab-btn")];
  const panels = [...document.querySelectorAll(".tab-panel")];

  function activate(tab) {
    buttons.forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
    panels.forEach((p) => p.classList.toggle("active", p.dataset.tabPanel === tab));
    // 방금 보인 패널은 그동안 display:none 이라 폭이 0이었으므로 폰트 크기를 다시 계산해야 함
    rescaleTextBoxes(document.body);
  }
  buttons.forEach((b) => b.addEventListener("click", () => activate(b.dataset.tab)));
  activate("blocks");
}

function populateBookSelect() {
  const sel = document.getElementById("bookSelect");
  sel.innerHTML = "";
  const og1 = el("optgroup", { label: "구약" });
  const og2 = el("optgroup", { label: "신약" });
  for (const b of state.books) {
    const opt = el("option", { value: b.abbr, text: b.name });
    (b.order < 39 ? og1 : og2).appendChild(opt);
  }
  sel.appendChild(og1);
  sel.appendChild(og2);
}

async function populateChaptersForBook() {
  const book = document.getElementById("bookSelect").value;
  const chapters = await apiJson(`api/chapters?book=${encodeURIComponent(book)}`);
  for (const id of ["startChapter", "endChapter"]) {
    const sel = document.getElementById(id);
    sel.innerHTML = "";
    for (const c of chapters) sel.appendChild(el("option", { value: c, text: `${c}장` }));
  }
}

// ---------- 구절 블록 ----------
function onAddBlock() {
  const book = document.getElementById("bookSelect").value;
  const bookName = state.books.find((b) => b.abbr === book).name;
  const startChapter = parseInt(document.getElementById("startChapter").value);
  const startVerse = parseInt(document.getElementById("startVerse").value) || 1;
  const endChapter = parseInt(document.getElementById("endChapter").value);
  const endVerse = parseInt(document.getElementById("endVerse").value) || 1;

  if (endChapter < startChapter || (endChapter === startChapter && endVerse < startVerse)) {
    alert("끝 위치가 시작 위치보다 앞설 수 없습니다");
    return;
  }
  state.blocks.push({ book, bookName, startChapter, startVerse, endChapter, endVerse });
  renderBlockList();
  recompute();
}

function removeBlock(i) {
  state.blocks.splice(i, 1);
  renderBlockList();
  recompute();
}

function moveBlock(i, dir) {
  const j = i + dir;
  if (j < 0 || j >= state.blocks.length) return;
  [state.blocks[i], state.blocks[j]] = [state.blocks[j], state.blocks[i]];
  renderBlockList();
  recompute();
}

function renderBlockList() {
  const ol = document.getElementById("blockList");
  ol.innerHTML = "";
  state.blocks.forEach((b, i) => {
    const label = formatRef(b.bookName, b.startChapter, b.startVerse, b.endChapter, b.endVerse);
    const upBtn = el("button", { class: "btn btn-sm", text: "▲", title: "위로" });
    upBtn.disabled = i === 0;
    upBtn.addEventListener("click", () => moveBlock(i, -1));
    const downBtn = el("button", { class: "btn btn-sm", text: "▼", title: "아래로" });
    downBtn.disabled = i === state.blocks.length - 1;
    downBtn.addEventListener("click", () => moveBlock(i, 1));
    ol.appendChild(el("li", {}, [
      el("span", { text: `${i + 1}. ${label}` }),
      el("span", { class: "block-actions" }, [
        upBtn, downBtn,
        el("button", { class: "btn btn-sm btn-danger", text: "삭제", onclick: () => removeBlock(i) }),
      ]),
    ]));
  });
}

// ---------- 조합/분배 ----------
async function recompute() {
  if (state.blocks.length === 0) {
    state.composed = { blockRefs: [], slides: [] };
  } else {
    try {
      state.composed = await apiJson("api/compose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          blocks: state.blocks.map(({ book, startChapter, startVerse, endChapter, endVerse }) => ({ book, startChapter, startVerse, endChapter, endVerse })),
          defaultGroupSize: state.defaultGroupSize,
          overrides: state.overrides,
        }),
      });
    } catch (e) {
      alert("구절 조합 오류: " + e.message);
      return;
    }
  }
  renderSlideList();
  renderCoverEditor();
  renderBodyEditor();
  renderFullPreview();
}

function renderSlideList() {
  // 슬라이드별 구절 수 조정은 "전체 미리보기" 단계(6번, renderFullPreview)에서
  // 실제 화면을 보며 하도록 옮기고, 여기서는 구성 요약만 간단히 보여준다.
  const wrap = document.getElementById("slideList");
  wrap.innerHTML = "";
  wrap.appendChild(el("div", { class: "slide-row" }, [
    el("span", { text: "표지" }),
    el("span", { class: "ref-text", text: state.composed.blockRefs.join(", ") }),
  ]));
  state.composed.slides.forEach((s, idx) => {
    wrap.appendChild(el("div", { class: "slide-row" }, [
      el("span", { text: `${idx + 1}` }),
      el("span", { class: "ref-text", text: s.refText }),
    ]));
  });
}

// ---------- 배경이미지 ----------
function renderGlobalBgGallery() {
  renderBgGallery(document.getElementById("globalBgGallery"), state.background, (ref) => {
    state.background = ref;
    renderGlobalBgGallery();
    renderFullPreview();
    renderCoverEditor();
    renderBodyEditor();
  });
}

function renderBgGallery(container, selectedRef, onPick) {
  container.innerHTML = "";
  const all = [
    ...state.defaultBackgrounds.map((b) => ({ ref: { defaultId: b.id }, name: b.name, file: b.file, userItem: false })),
    ...state.userBackgrounds.map((b) => ({ ref: { uploadId: b.id }, name: b.name, file: b.file, userItem: true })),
  ];
  for (const item of all) {
    const isSelected = selectedRef && ((item.ref.defaultId && item.ref.defaultId === selectedRef.defaultId) ||
      (item.ref.uploadId && item.ref.uploadId === selectedRef.uploadId));
    const url = item.userItem ? `user-bg/${item.file}` : `static/backgrounds/default/${item.file}`;
    const thumb = el("div", {
      class: "bg-thumb" + (isSelected ? " selected" : ""),
      style: `background-image:url('${url}')`,
      onclick: () => onPick(item.ref),
    }, [el("span", { class: "label", text: item.name })]);
    if (item.userItem) {
      thumb.appendChild(el("button", {
        class: "del", text: "×",
        onclick: (e) => { e.stopPropagation(); deleteUserBackground(item.file); },
      }));
    }
    container.appendChild(thumb);
  }
}

async function onUploadBackground(e) {
  const file = e.target.files[0];
  if (!file) return;
  const status = document.getElementById("uploadStatus");
  status.textContent = "업로드 중...";
  const fd = new FormData();
  fd.append("file", file);
  try {
    await apiJson("api/backgrounds/upload", { method: "POST", body: fd });
    const bgData = await apiJson("api/backgrounds");
    state.defaultBackgrounds = bgData.default;
    state.userBackgrounds = bgData.user;
    renderGlobalBgGallery();
    status.textContent = "업로드 완료";
  } catch (err) {
    status.textContent = "업로드 실패: " + err.message;
  }
  e.target.value = "";
}

async function deleteUserBackground(filename) {
  await apiJson(`api/backgrounds/user/${encodeURIComponent(filename)}`, { method: "DELETE" });
  const bgData = await apiJson("api/backgrounds");
  state.defaultBackgrounds = bgData.default;
  state.userBackgrounds = bgData.user;
  renderGlobalBgGallery();
  renderFullPreview();
}

function openBgPicker(target) {
  state.bgPickerTarget = target;
  const overlay = document.getElementById("bgPickerOverlay");
  overlay.classList.remove("hidden");
  const current = target === "global" ? state.background : (state.slideBackgrounds[target] || null);
  renderBgGallery(document.getElementById("bgPickerGallery"), current, (ref) => {
    if (target === "global") state.background = ref;
    else state.slideBackgrounds[target] = ref;
    closeBgPicker();
    renderFullPreview();
    renderGlobalBgGallery();
  });
}
function closeBgPicker() {
  document.getElementById("bgPickerOverlay").classList.add("hidden");
}

// ---------- 표지/본문 편집기 (드래그 가능한 위치) ----------
function attachDrag(boxEl, containerEl, style, onChange) {
  boxEl.addEventListener("mousedown", (ev) => {
    ev.preventDefault();
    const rect = containerEl.getBoundingClientRect();
    const startX = ev.clientX, startY = ev.clientY;
    const startLeft = style.xPct * rect.width, startTop = style.yPct * rect.height;
    function onMove(mv) {
      const dx = mv.clientX - startX, dy = mv.clientY - startY;
      let left = startLeft + dx, top = startTop + dy;
      const w = style.wPct * rect.width, h = style.hPct * rect.height;
      left = Math.max(0, Math.min(rect.width - w, left));
      top = Math.max(0, Math.min(rect.height - h, top));
      boxEl.style.left = left + "px";
      boxEl.style.top = top + "px";
      style.xPct = left / rect.width;
      style.yPct = top / rect.height;
    }
    function onUp() {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      onChange();
    }
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  });
}

function applyOverlayStyle(boxEl, style) {
  boxEl.style.left = (style.xPct * 100) + "%";
  boxEl.style.top = (style.yPct * 100) + "%";
  boxEl.style.width = (style.wPct * 100) + "%";
  boxEl.style.height = (style.hPct * 100) + "%";
  boxEl.style.background = hexToRgba(style.color, style.opacity);
  boxEl.style.borderRadius = style.shape === "ellipse" ? "50%" : style.shape === "rounded-rect" ? "5%" : "0";
}

// PPT 슬라이드 폭(13.333in = 960pt) 기준. 미리보기 박스의 실제 렌더링 폭에 맞춰
// 폰트 크기를 스케일해야 큰 편집 박스와 작은 전체 미리보기 썸네일에서 글자 비율이 같다.
const SLIDE_W_PT = 960;
// 절 번호 라벨("30. ", "18~19. " 등)의 렌더링 폭을 문자별 상대폭(em)으로 근사한다.
// 값은 브라우저에서 실측(getBoundingClientRect)해 캘리브레이션한 것으로
// app/ppt_builder.py의 _label_indent_pt와 반드시 맞춰야 한다.
const CHAR_EM_WIDTH = { ".": 0.30, " ": 0.313, "~": 0.72 };
const DIGIT_EM_WIDTH = 0.58;
function labelIndentPt(label, fontSizePt) {
  let totalEm = 0;
  for (const ch of label) totalEm += (ch >= "0" && ch <= "9") ? DIGIT_EM_WIDTH : (CHAR_EM_WIDTH[ch] ?? 0.5);
  return totalEm * fontSizePt;
}

function applyTextBoxStyle(boxEl, style, text) {
  boxEl.style.left = (style.xPct * 100) + "%";
  boxEl.style.top = (style.yPct * 100) + "%";
  boxEl.style.width = (style.wPct * 100) + "%";
  boxEl.style.height = (style.hPct * 100) + "%";
  boxEl.dataset.ptSize = style.fontSize;
  boxEl.style.color = style.color;
  boxEl.style.fontWeight = style.bold ? "bold" : "normal";
  boxEl.style.fontFamily = `"${style.fontFamily || "맑은 고딕"}", "Apple SD Gothic Neo", sans-serif`;
  boxEl.style.justifyContent = style.align === "left" ? "flex-start" : style.align === "right" ? "flex-end" : "center";
  boxEl.style.textAlign = style.align || "center";
  boxEl.textContent = text || "";
}

function verseNumberLabel(v) {
  return (v.vEnd && v.vEnd !== v.v) ? `${v.v}~${v.vEnd}. ` : `${v.v}. `;
}

// 절의 고유 식별자(책+장+절범위). 어느 슬라이드에 배치되든 이 값으로 수동
// 줄바꿈(state.manualBreaks) 을 일관되게 찾아 적용한다.
function verseKey(v) {
  return `${v.book}:${v.chapter}:${v.v}:${v.vEnd}`;
}

function effectiveVerseText(v) {
  return state.manualBreaks[verseKey(v)] ?? v.text;
}

// contentEditable 요소의 내용을 "\n"으로 구분된 일반 텍스트로 되돌린다
// (<br> 는 줄바꿈으로, 그 외 텍스트 노드는 그대로 이어붙임).
function editableToText(el) {
  let out = "";
  el.childNodes.forEach((node) => {
    if (node.nodeName === "BR") out += "\n";
    else out += node.textContent;
  });
  return out;
}

function renderTextWithBreaks(container, text) {
  container.innerHTML = "";
  const lines = String(text).split("\n");
  lines.forEach((line, i) => {
    container.appendChild(document.createTextNode(line));
    if (i < lines.length - 1) container.appendChild(document.createElement("br"));
  });
}

// 절 번호(강조색) + 본문을 절마다 한 문단으로 렌더링. PPT의 _add_verse_textbox와 대응.
// 본문 텍스트 부분은 편집 가능해서, 사용자가 원하는 위치에 커서를 두고 Enter를
// 누르면 그 지점에서 강제 줄바꿈되고(state.manualBreaks에 저장) PPT 생성 시에도
// 그대로 반영된다.
function applyVerseTextBox(boxEl, style, verses) {
  boxEl.style.left = (style.xPct * 100) + "%";
  boxEl.style.top = (style.yPct * 100) + "%";
  boxEl.style.width = (style.wPct * 100) + "%";
  boxEl.style.height = (style.hPct * 100) + "%";
  boxEl.dataset.ptSize = style.fontSize;
  boxEl.style.fontWeight = style.bold ? "bold" : "normal";
  boxEl.style.fontFamily = `"${style.fontFamily || "맑은 고딕"}", "Apple SD Gothic Neo", sans-serif`;
  boxEl.style.flexDirection = "column";
  boxEl.style.alignItems = style.align === "left" ? "flex-start" : style.align === "right" ? "flex-end" : "center";
  boxEl.style.justifyContent = "center";
  boxEl.style.textAlign = style.align || "left";
  boxEl.innerHTML = "";
  const verseSpacing = style.verseSpacing ?? 10;
  verses.forEach((v, i) => {
    const p = el("div", {});
    if (i < verses.length - 1) p.dataset.ptGap = verseSpacing;
    const label = verseNumberLabel(v);
    if (style.align === "left") p.dataset.indentPt = labelIndentPt(label, style.fontSize || 26);
    p.appendChild(el("span", { text: label, style: `color:${style.numberColor || style.color};font-weight:${style.numberBold ? "bold" : "normal"}` }));

    const textSpan = el("span", { contenteditable: "true", spellcheck: "false", class: "verse-text-editable" });
    textSpan.style.color = style.color;
    renderTextWithBreaks(textSpan, effectiveVerseText(v));
    // 편집 박스(coverPreview/bodyPreview)에서는 부모 text-box에 드래그(위치 이동)가
    // 붙어 있어서, 텍스트 클릭이 드래그로 오인되지 않도록 이벤트 전파를 막는다.
    textSpan.addEventListener("mousedown", (e) => e.stopPropagation());
    textSpan.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        document.execCommand("insertLineBreak");
      }
    });
    textSpan.addEventListener("blur", () => {
      const newText = editableToText(textSpan);
      if (newText === effectiveVerseText(v)) return; // 변경 없으면 재렌더 생략(다른 절 클릭 방해 방지)
      const key = verseKey(v);
      if (newText === v.text) delete state.manualBreaks[key];
      else state.manualBreaks[key] = newText;
      renderFullPreview();
      renderBodyEditor();
    });
    p.appendChild(textSpan);
    boxEl.appendChild(p);
  });
}

// 실제 렌더링된 slide-box 폭을 기준으로 text-box 폰트 크기(px)를 계산해 적용한다.
// rootEl 자신이 .slide-box인 경우(coverPreview/bodyPreview 편집 박스)도 포함해야 한다.
// querySelectorAll은 자손만 찾고 rootEl 자신은 매칭하지 않기 때문.
function rescaleTextBoxes(rootEl) {
  const boxes = rootEl.matches && rootEl.matches(".slide-box")
    ? [rootEl, ...rootEl.querySelectorAll(".slide-box")]
    : [...rootEl.querySelectorAll(".slide-box")];
  boxes.forEach((box) => {
    const scale = box.clientWidth / SLIDE_W_PT;
    box.querySelectorAll(".text-box").forEach((tb) => {
      const pt = parseFloat(tb.dataset.ptSize || "20");
      tb.style.fontSize = (pt * scale) + "px";
      tb.querySelectorAll("[data-pt-gap]").forEach((p) => {
        p.style.marginBottom = (parseFloat(p.dataset.ptGap) * scale) + "px";
      });
      tb.querySelectorAll("[data-indent-pt]").forEach((p) => {
        const px = parseFloat(p.dataset.indentPt) * scale;
        p.style.paddingLeft = px + "px";
        p.style.textIndent = (-px) + "px";
      });
    });
  });
}

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// 컨트롤 패널 안의 텍스트/숫자 입력은 "input" 이벤트로 프리뷰만 즉시 갱신한다
// (패널을 다시 그리면 입력 중이던 요소가 사라져 포커스가 끊긴다).
// 반대로 드래그는 입력 포커스가 없는 조작이라 끝난 뒤 컨트롤 패널까지 함께
// 다시 그려서 옮겨진 X/Y 값이 숫자 입력칸에도 반영되게 한다.
function refreshCoverPreview() { recordThemeChange(); renderCoverEditor(); renderFullPreview(); }
function refreshCoverAll() { recordThemeChange(); renderCoverEditor(); renderCoverControls(); renderFullPreview(); }
function refreshBodyPreview() { recordThemeChange(); renderBodyEditor(); renderFullPreview(); }
function refreshBodyAll() { recordThemeChange(); renderBodyEditor(); renderBodyControls(); renderFullPreview(); }

// ---------- 표지/본문 서식 실행취소·재실행 ----------
// 위 refresh 함수들은 표지/본문 편집(드래그 이동, 색상/폰트/위치 등 모든 서식
// 변경)의 유일한 공통 경로라서, 여기서 recordThemeChange()를 한 번만 걸어주면
// 모든 편집 동작이 자동으로 히스토리에 잡힌다. 타이핑/드래그처럼 "input" 이벤트가
// 연속으로 쏟아지는 조작은 한 글자/한 픽셀마다 실행취소 단계가 생기면 오히려
// 불편하므로, 조작이 멈추고 일정 시간(HISTORY_DEBOUNCE_MS) 지날 때까지 커밋을
// 미뤄서 하나의 실행취소 단계로 묶는다.
const HISTORY_LIMIT = 60;
const HISTORY_DEBOUNCE_MS = 500;
let undoStack = [];
let redoStack = [];
let lastThemeSnapshot = null;
let historyDebounceTimer = null;

function resetHistory() {
  clearTimeout(historyDebounceTimer);
  undoStack = [];
  redoStack = [];
  lastThemeSnapshot = JSON.stringify(state.theme);
  updateUndoRedoButtons();
}

function commitThemeSnapshot() {
  clearTimeout(historyDebounceTimer);
  const current = JSON.stringify(state.theme);
  if (current === lastThemeSnapshot) return;
  undoStack.push(lastThemeSnapshot);
  if (undoStack.length > HISTORY_LIMIT) undoStack.shift();
  redoStack = [];
  lastThemeSnapshot = current;
  updateUndoRedoButtons();
}

function recordThemeChange() {
  clearTimeout(historyDebounceTimer);
  historyDebounceTimer = setTimeout(commitThemeSnapshot, HISTORY_DEBOUNCE_MS);
  updateUndoRedoButtons();
}

function undoTheme() {
  commitThemeSnapshot();
  if (undoStack.length === 0) return;
  redoStack.push(lastThemeSnapshot);
  const prev = undoStack.pop();
  state.theme = JSON.parse(prev);
  lastThemeSnapshot = prev;
  renderCoverEditor();
  renderCoverControls();
  renderBodyEditor();
  renderBodyControls();
  renderFullPreview();
  updateUndoRedoButtons();
}

function redoTheme() {
  if (redoStack.length === 0) return;
  undoStack.push(lastThemeSnapshot);
  const next = redoStack.pop();
  state.theme = JSON.parse(next);
  lastThemeSnapshot = next;
  renderCoverEditor();
  renderCoverControls();
  renderBodyEditor();
  renderBodyControls();
  renderFullPreview();
  updateUndoRedoButtons();
}

function updateUndoRedoButtons() {
  const canUndo = undoStack.length > 0 || JSON.stringify(state.theme) !== lastThemeSnapshot;
  const canRedo = redoStack.length > 0;
  for (const id of ["coverUndoBtn", "bodyUndoBtn"]) {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !canUndo;
  }
  for (const id of ["coverRedoBtn", "bodyRedoBtn"]) {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !canRedo;
  }
}

function renderCoverEditor() {
  const preview = document.getElementById("coverPreview");
  preview.innerHTML = "";
  preview.style.backgroundImage = state.background ? `url('${bgUrl(state.background)}')` : "";

  const cover = state.theme.cover;

  if (cover.overlay.enabled) {
    const ov = el("div", { class: "slide-overlay" });
    applyOverlayStyle(ov, cover.overlay);
    attachDrag(ov, preview, cover.overlay, refreshCoverAll);
    preview.appendChild(ov);
  }

  const refText = state.composed.blockRefs.join(", ") || "(구절을 추가하면 표시됩니다)";
  const lines = [
    { key: "title", style: cover.title, text: cover.title.text },
    { key: "verseRef", style: cover.verseRef, text: refText },
  ];
  if (cover.presenter.show !== false) {
    lines.push({ key: "presenter", style: cover.presenter, text: cover.presenter.text || "(발표자 이름)" });
  }
  for (const line of lines) {
    const box = el("div", { class: "text-box" });
    applyTextBoxStyle(box, line.style, line.text);
    attachDrag(box, preview, line.style, refreshCoverAll);
    preview.appendChild(box);
  }
  rescaleTextBoxes(preview);
}

function renderCoverControls() {
  const wrap = document.getElementById("coverControls");
  wrap.innerHTML = "";
  const cover = state.theme.cover;

  wrap.appendChild(buildLineControl("1행 · 타이틀", cover.title, {
    hasText: true, presets: TITLE_PRESETS, onChange: refreshCoverPreview,
  }));
  wrap.appendChild(buildLineControl("2행 · 구절 표시 (자동)", cover.verseRef, {
    hasText: false, onChange: refreshCoverPreview,
  }));
  wrap.appendChild(buildLineControl("3행 · 발표자", cover.presenter, {
    hasText: true, hasShowToggle: true, textPlaceholder: "예: 김형균 집사", onChange: refreshCoverPreview,
  }));
  wrap.appendChild(buildOverlayControl("가독성 오버레이", cover.overlay, refreshCoverPreview));
}

function renderBodyEditor() {
  const preview = document.getElementById("bodyPreview");
  preview.innerHTML = "";
  preview.style.backgroundImage = state.background ? `url('${bgUrl(state.background)}')` : "";

  const body = state.theme.body;
  const sample = state.composed.slides[0];
  const sampleVerses = sample ? sample.verses : [{ v: 30, vEnd: 30, text: "(구절을 추가하면 본문 예시가 표시됩니다)" }];
  const sampleRef = sample ? sample.refText : "책 장:절~절";

  if (body.overlay.enabled) {
    const ov = el("div", { class: "slide-overlay" });
    applyOverlayStyle(ov, body.overlay);
    attachDrag(ov, preview, body.overlay, refreshBodyAll);
    preview.appendChild(ov);
  }

  if (body.refTitle.show) {
    const tBox = el("div", { class: "text-box" });
    applyTextBoxStyle(tBox, body.refTitle, sampleRef);
    attachDrag(tBox, preview, body.refTitle, refreshBodyAll);
    preview.appendChild(tBox);
  }

  const vBox = el("div", { class: "text-box" });
  applyVerseTextBox(vBox, body.verseText, sampleVerses);
  attachDrag(vBox, preview, body.verseText, refreshBodyAll);
  preview.appendChild(vBox);

  rescaleTextBoxes(preview);
}

function renderBodyControls() {
  const wrap = document.getElementById("bodyControls");
  wrap.innerHTML = "";
  const body = state.theme.body;
  wrap.appendChild(buildLineControl("구절 범위 제목 (예: 마가복음 6:30~32)", body.refTitle, {
    hasText: false, hasShowToggle: true, onChange: refreshBodyPreview,
  }));
  wrap.appendChild(buildLineControl("구절 본문 (절 번호 + 본문)", body.verseText, {
    hasText: false, hasNumberColor: true, hasVerseSpacing: true, onChange: refreshBodyPreview,
  }));
  wrap.appendChild(buildOverlayControl("가독성 오버레이", body.overlay, refreshBodyPreview));
}

function buildLineControl(title, style, opts) {
  const box = el("div", { class: "line-control" });
  box.appendChild(el("h4", { text: title }));

  if (opts.hasShowToggle) {
    const chk = el("input", { type: "checkbox" });
    chk.checked = style.show !== false;
    chk.addEventListener("change", () => { style.show = chk.checked; opts.onChange(); });
    box.appendChild(el("label", { class: "row" }, [chk, el("span", { text: "표시함" })]));
  }

  if (opts.hasText) {
    if (opts.presets) {
      const presetSel = el("select", {});
      presetSel.appendChild(el("option", { value: "", text: "-- 프리셋 선택 --" }));
      for (const p of opts.presets) presetSel.appendChild(el("option", { value: p, text: p }));
      presetSel.addEventListener("change", () => {
        if (presetSel.value) { style.text = presetSel.value; textInput.value = presetSel.value; opts.onChange(); }
      });
      box.appendChild(el("div", { class: "row" }, [presetSel]));
    }
    const textInput = el("input", { type: "text", placeholder: opts.textPlaceholder || "" });
    textInput.value = style.text || "";
    textInput.addEventListener("input", () => { style.text = textInput.value; opts.onChange(); });
    box.appendChild(el("div", { class: "row" }, [textInput]));
  }

  const posRow = el("div", { class: "row" });
  for (const [key, labelText] of [["xPct", "X%"], ["yPct", "Y%"], ["wPct", "W%"], ["hPct", "H%"]]) {
    const input = el("input", { type: "number", min: "0", max: "100", step: "1" });
    input.value = Math.round(style[key] * 100);
    input.addEventListener("input", () => { style[key] = (parseFloat(input.value) || 0) / 100; opts.onChange(); });
    posRow.appendChild(el("label", {}, [el("span", { text: labelText }), input]));
  }
  box.appendChild(posRow);

  const styleRow = el("div", { class: "row" });
  const sizeInput = el("input", { type: "number", min: "6", max: "150" });
  sizeInput.value = style.fontSize;
  sizeInput.addEventListener("input", () => { style.fontSize = parseFloat(sizeInput.value) || 20; opts.onChange(); });
  styleRow.appendChild(el("label", {}, [el("span", { text: "크기" }), sizeInput]));

  const colorInput = el("input", { type: "color" });
  colorInput.value = style.color;
  colorInput.addEventListener("input", () => { style.color = colorInput.value; opts.onChange(); });
  styleRow.appendChild(el("label", {}, [el("span", { text: "색상" }), colorInput]));

  const boldChk = el("input", { type: "checkbox" });
  boldChk.checked = !!style.bold;
  boldChk.addEventListener("change", () => { style.bold = boldChk.checked; opts.onChange(); });
  styleRow.appendChild(el("label", {}, [boldChk, el("span", { text: "굵게" })]));

  const alignSel = el("select", {});
  for (const [v, t] of [["left", "왼쪽"], ["center", "가운데"], ["right", "오른쪽"]]) alignSel.appendChild(el("option", { value: v, text: t }));
  alignSel.value = style.align || "center";
  alignSel.addEventListener("change", () => { style.align = alignSel.value; opts.onChange(); });
  styleRow.appendChild(el("label", {}, [el("span", { text: "정렬" }), alignSel]));

  box.appendChild(styleRow);

  if (opts.hasNumberColor) {
    const numRow = el("div", { class: "row" });
    const numColorInput = el("input", { type: "color" });
    numColorInput.value = style.numberColor || style.color;
    numColorInput.addEventListener("input", () => { style.numberColor = numColorInput.value; opts.onChange(); });
    numRow.appendChild(el("label", {}, [el("span", { text: "번호 색상" }), numColorInput]));

    const numBoldChk = el("input", { type: "checkbox" });
    numBoldChk.checked = !!style.numberBold;
    numBoldChk.addEventListener("change", () => { style.numberBold = numBoldChk.checked; opts.onChange(); });
    numRow.appendChild(el("label", {}, [numBoldChk, el("span", { text: "번호 굵게" })]));
    box.appendChild(numRow);
  }

  if (opts.hasVerseSpacing) {
    const spacingRow = el("div", { class: "row" });
    const spacingInput = el("input", { type: "number", min: "0", max: "80", step: "1" });
    spacingInput.value = style.verseSpacing ?? 10;
    spacingInput.addEventListener("input", () => { style.verseSpacing = parseFloat(spacingInput.value) || 0; opts.onChange(); });
    spacingRow.appendChild(el("label", {}, [el("span", { text: "절 간격(pt)" }), spacingInput]));
    box.appendChild(spacingRow);
  }

  const fontRow = el("div", { class: "row" });
  fontRow.appendChild(el("label", {}, [el("span", { text: "폰트" }), buildFontPicker(style, opts.onChange)]));
  box.appendChild(fontRow);

  return box;
}

// datalist는 WKWebView(pywebview의 macOS 브라우저 엔진)에서 자동완성
// 드롭다운을 사실상 렌더링하지 않아서, 직접 그리는 목록으로 대체한다.
function buildFontPicker(style, onChange) {
  const wrap = el("div", { class: "font-autocomplete" });
  const input = el("input", { type: "text", autocomplete: "off" });
  input.value = style.fontFamily || "맑은 고딕";
  const list = el("div", { class: "font-suggestions" });

  function renderList(matches) {
    list.innerHTML = "";
    if (matches.length === 0) { list.classList.remove("open"); return; }
    for (const f of matches) {
      const item = el("div", { class: "item", text: f });
      item.style.fontFamily = `"${f}"`;
      item.addEventListener("mousedown", (ev) => {
        ev.preventDefault(); // blur보다 먼저 처리되도록
        input.value = f;
        style.fontFamily = f;
        list.classList.remove("open");
        onChange();
      });
      list.appendChild(item);
    }
    list.classList.add("open");
  }

  // 입력값이 실제 폰트 이름과 정확히 일치하지 않아도(예: 기본값 "맑은 고딕")
  // 포커스만 해도 전체 목록이 보이도록, 필터링 없이 상위 목록을 먼저 보여준다.
  function renderFiltered() {
    const q = input.value.trim().toLowerCase();
    const matches = q ? state.fonts.filter((f) => f.toLowerCase().includes(q)).slice(0, 60) : state.fonts.slice(0, 60);
    renderList(matches);
  }

  input.addEventListener("input", () => { style.fontFamily = input.value; onChange(); renderFiltered(); });
  input.addEventListener("focus", () => renderList(state.fonts.slice(0, 60)));
  input.addEventListener("blur", () => setTimeout(() => list.classList.remove("open"), 150));

  wrap.appendChild(input);
  wrap.appendChild(list);
  return wrap;
}

function buildOverlayControl(title, style, onChange) {
  const box = el("div", { class: "line-control" });
  box.appendChild(el("h4", { text: title }));

  const enabledChk = el("input", { type: "checkbox" });
  enabledChk.checked = !!style.enabled;
  enabledChk.addEventListener("change", () => { style.enabled = enabledChk.checked; onChange(); });
  box.appendChild(el("label", { class: "row" }, [enabledChk, el("span", { text: "사용함 (배경과 글자 사이에 반투명 레이어 배치)" })]));

  const shapeRow = el("div", { class: "row" });
  const shapeSel = el("select", {});
  for (const [v, t] of [["rect", "사각형"], ["rounded-rect", "둥근 사각형"], ["ellipse", "타원"]]) {
    shapeSel.appendChild(el("option", { value: v, text: t }));
  }
  shapeSel.value = style.shape || "rect";
  shapeSel.addEventListener("change", () => { style.shape = shapeSel.value; onChange(); });
  shapeRow.appendChild(el("label", {}, [el("span", { text: "모양" }), shapeSel]));

  const colorInput = el("input", { type: "color" });
  colorInput.value = style.color;
  colorInput.addEventListener("input", () => { style.color = colorInput.value; onChange(); });
  shapeRow.appendChild(el("label", {}, [el("span", { text: "색상" }), colorInput]));

  const opacityInput = el("input", { type: "number", min: "0", max: "100", step: "5" });
  opacityInput.value = Math.round(style.opacity * 100);
  opacityInput.addEventListener("input", () => { style.opacity = (parseFloat(opacityInput.value) || 0) / 100; onChange(); });
  shapeRow.appendChild(el("label", {}, [el("span", { text: "투명도%" }), opacityInput]));
  box.appendChild(shapeRow);

  const posRow = el("div", { class: "row" });
  for (const [key, labelText] of [["xPct", "X%"], ["yPct", "Y%"], ["wPct", "W%"], ["hPct", "H%"]]) {
    const input = el("input", { type: "number", min: "0", max: "100", step: "1" });
    input.value = Math.round(style[key] * 100);
    input.addEventListener("input", () => { style[key] = (parseFloat(input.value) || 0) / 100; onChange(); });
    posRow.appendChild(el("label", {}, [el("span", { text: labelText }), input]));
  }
  box.appendChild(posRow);

  return box;
}

// ---------- 전체 미리보기 ----------
function renderFullPreview() {
  const wrap = document.getElementById("fullPreview");
  wrap.innerHTML = "";
  const total = 1 + state.composed.slides.length;
  document.getElementById("slideCount").textContent = total;

  // 표지
  const coverLines = [
    { style: state.theme.cover.title, text: state.theme.cover.title.text },
    { style: state.theme.cover.verseRef, text: state.composed.blockRefs.join(", ") },
  ];
  if (state.theme.cover.presenter.show !== false) {
    coverLines.push({ style: state.theme.cover.presenter, text: state.theme.cover.presenter.text });
  }
  wrap.appendChild(buildPreviewItem(0, "표지", state.background, coverLines, null, state.theme.cover.overlay));

  state.composed.slides.forEach((s, idx) => {
    const key = idx + 1;
    const bgRef = state.slideBackgrounds[key] || state.background;
    const lines = [];
    if (state.theme.body.refTitle.show) lines.push({ style: state.theme.body.refTitle, text: s.refText });
    lines.push({ style: state.theme.body.verseText, verses: s.verses });
    const count = state.overrides[idx] ?? state.defaultGroupSize;
    wrap.appendChild(buildPreviewItem(key, `${key + 1}`, bgRef, lines, {
      value: count,
      onChange: (v) => { state.overrides[idx] = v; recompute(); },
    }, state.theme.body.overlay));
  });
  rescaleTextBoxes(wrap);
}

function buildPreviewItem(key, label, bgRef, lines, countInfo, overlayStyle) {
  const box = el("div", { class: "slide-box" });
  box.style.backgroundImage = bgRef ? `url('${bgUrl(bgRef)}')` : "";
  if (overlayStyle && overlayStyle.enabled) {
    const ov = el("div", { class: "slide-overlay" });
    applyOverlayStyle(ov, overlayStyle);
    box.appendChild(ov);
  }
  for (const line of lines) {
    const t = el("div", { class: "text-box" });
    if (line.verses) applyVerseTextBox(t, line.style, line.verses);
    else applyTextBoxStyle(t, line.style, line.text);
    box.appendChild(t);
  }
  const captionChildren = [el("span", { text: label })];
  if (countInfo) {
    const countInput = el("input", { type: "number", min: "1", value: countInfo.value, class: "count-input" });
    countInput.addEventListener("change", () => countInfo.onChange(parseInt(countInput.value) || 1));
    captionChildren.push(el("label", { class: "count-label" }, [el("span", { text: "구절 수" }), countInput]));
  }
  captionChildren.push(el("button", { class: "btn btn-sm", text: "배경 변경", onclick: () => openBgPicker(key) }));
  const caption = el("div", { class: "caption" }, captionChildren);
  return el("div", { class: "item" }, [box, caption]);
}

// ---------- 테마 ----------
function renderThemeSelect() {
  const sel = document.getElementById("themeSelect");
  sel.innerHTML = "";
  sel.appendChild(el("option", { value: "", text: "-- 저장된 테마 불러오기 --" }));
  for (const t of state.themesList) sel.appendChild(el("option", { value: t.name, text: t.name }));
}

async function onSaveTheme() {
  const name = document.getElementById("themeNameInput").value.trim();
  if (!name) { alert("테마 이름을 입력하세요"); return; }
  state.themesList = await apiJson("api/themes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, cover: state.theme.cover, body: state.theme.body }),
  });
  renderThemeSelect();
  document.getElementById("themeSelect").value = name;
  alert("테마가 저장되었습니다");
}

function onLoadTheme() {
  const name = document.getElementById("themeSelect").value;
  if (!name) return;
  const t = state.themesList.find((x) => x.name === name);
  if (!t) return;
  // 부족한 필드(과거 저장된 테마에 새로 추가된 항목이 없을 수 있음)는 현재 기본값을 유지
  for (const key of ["title", "verseRef", "presenter", "overlay"]) {
    if (t.cover && t.cover[key]) state.theme.cover[key] = { ...state.theme.cover[key], ...t.cover[key] };
  }
  for (const key of ["refTitle", "verseText", "overlay"]) {
    if (t.body && t.body[key]) state.theme.body[key] = { ...state.theme.body[key], ...t.body[key] };
  }
  document.getElementById("themeNameInput").value = name;
  renderCoverEditor();
  renderBodyEditor();
  renderCoverControls();
  renderBodyControls();
  renderFullPreview();
  resetHistory();
}

// ---------- 작업(구절/분배/배경/테마 전체 상태) 저장·불러오기 ----------
function renderProjectSelect() {
  const sel = document.getElementById("projectSelect");
  sel.innerHTML = "";
  sel.appendChild(el("option", { value: "", text: "-- 저장된 작업 불러오기 --" }));
  for (const p of state.projectsList) sel.appendChild(el("option", { value: p.name, text: p.name }));
}

async function onSaveProject() {
  const name = document.getElementById("projectNameInput").value.trim();
  if (!name) { alert("작업 이름을 입력하세요"); return; }
  const snapshot = {
    name,
    blocks: state.blocks,
    defaultGroupSize: state.defaultGroupSize,
    overrides: state.overrides,
    background: state.background,
    slideBackgrounds: state.slideBackgrounds,
    theme: state.theme,
    manualBreaks: state.manualBreaks,
  };
  state.projectsList = await apiJson("api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(snapshot),
  });
  renderProjectSelect();
  document.getElementById("projectSelect").value = name;
  alert("작업이 저장되었습니다");
}

async function onLoadProject() {
  const name = document.getElementById("projectSelect").value;
  if (!name) return;
  const proj = state.projectsList.find((x) => x.name === name);
  if (!proj) return;

  state.blocks = proj.blocks || [];
  state.defaultGroupSize = proj.defaultGroupSize ?? 2;
  state.overrides = proj.overrides || [];
  state.background = proj.background || state.background;
  state.slideBackgrounds = proj.slideBackgrounds || {};
  state.manualBreaks = proj.manualBreaks || {};
  // 테마와 마찬가지로 저장 당시에 없던 필드는 현재 기본값을 유지
  if (proj.theme) {
    for (const key of ["title", "verseRef", "presenter", "overlay"]) {
      if (proj.theme.cover && proj.theme.cover[key]) state.theme.cover[key] = { ...state.theme.cover[key], ...proj.theme.cover[key] };
    }
    for (const key of ["refTitle", "verseText", "overlay"]) {
      if (proj.theme.body && proj.theme.body[key]) state.theme.body[key] = { ...state.theme.body[key], ...proj.theme.body[key] };
    }
  }

  document.getElementById("projectNameInput").value = name;
  document.getElementById("defaultGroupSize").value = state.defaultGroupSize;
  renderBlockList();
  renderGlobalBgGallery();
  renderCoverEditor();
  renderBodyEditor();
  renderCoverControls();
  renderBodyControls();
  await recompute();
  resetHistory();
}

function onNewProject() {
  if (state.blocks.length > 0 && !confirm("저장하지 않은 현재 작업 내용이 사라집니다. 새 작업을 시작할까요?")) return;
  state.blocks = [];
  state.overrides = [];
  state.slideBackgrounds = {};
  state.manualBreaks = {};
  state.defaultGroupSize = 2;
  document.getElementById("defaultGroupSize").value = 2;
  document.getElementById("projectSelect").value = "";
  document.getElementById("projectNameInput").value = "";
  renderBlockList();
  recompute();
}

// ---------- 생성 ----------
async function onGenerate() {
  if (state.blocks.length === 0) { alert("구절을 먼저 추가하세요"); return; }
  const btns = [document.getElementById("generateBtn"), document.getElementById("generateBtnBottom")];
  const originalText = btns[0].textContent;
  for (const b of btns) { b.disabled = true; b.textContent = "생성 중..."; }
  try {
    const res = await api("api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        blocks: state.blocks.map(({ book, startChapter, startVerse, endChapter, endVerse }) => ({ book, startChapter, startVerse, endChapter, endVerse })),
        defaultGroupSize: state.defaultGroupSize,
        overrides: state.overrides,
        background: state.background,
        slideBackgrounds: state.slideBackgrounds,
        theme: state.theme,
        manualBreaks: state.manualBreaks,
      }),
    });
    const blob = await res.blob();
    await savePptxBlob(blob, "성경말씀.pptx");
  } catch (e) {
    alert("생성 실패: " + e.message);
  } finally {
    for (const b of btns) { b.disabled = false; b.textContent = originalText; }
  }
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

// 데스크톱 앱(pywebview) 안에서는 브라우저의 <a download> 방식이 동작하지
// 않는 경우가 많아, 네이티브 "다른 이름으로 저장" 대화상자를 통해 저장한다.
// 일반 브라우저(개발 중 테스트 등)에서는 기존 방식으로 자동 다운로드한다.
async function savePptxBlob(blob, filename) {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.save_pptx) {
    const base64 = await blobToBase64(blob);
    const result = await window.pywebview.api.save_pptx(base64, filename);
    if (result && result.ok) {
      alert("저장 완료:\n" + result.path);
    } else if (result && !result.cancelled) {
      alert("저장 실패: " + (result.error || "알 수 없는 오류"));
    }
    return;
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

init();
