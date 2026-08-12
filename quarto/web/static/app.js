const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const pendingPanel = document.getElementById("pending-piece-panel");
const pendingPieceEl = document.getElementById("pending-piece");
const selectPanel = document.getElementById("select-panel");
const pickerEl = document.getElementById("piece-picker");
const logEl = document.getElementById("log");
const newGameBtn = document.getElementById("new-game-btn");
const firstPlayerSelect = document.getElementById("first-player");
const squaresRuleCheckbox = document.getElementById("squares-rule");

let currentState = null;

function pieceSvg(id, { size = 52 } = {}) {
  const tall = (id & 1) !== 0;
  const dark = (id & 2) !== 0;
  const round = (id & 4) !== 0;
  const solid = (id & 8) !== 0;

  const color = dark ? "#2a2c33" : "#ece6d8";
  const rimStroke = dark ? "#565b68" : "#111214";
  const r = tall ? 24 : 16;
  const cx = size / 2;
  const cy = size / 2;

  let shape;
  if (solid) {
    if (round) {
      shape = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${color}" stroke="${rimStroke}" stroke-width="1.5"/>`;
    } else {
      shape = `<rect x="${cx - r}" y="${cy - r}" width="${r * 2}" height="${r * 2}" rx="6" fill="${color}" stroke="${rimStroke}" stroke-width="1.5"/>`;
    }
  } else {
    const strokeWidth = tall ? 9 : 7;
    if (round) {
      shape = `<circle cx="${cx}" cy="${cy}" r="${r - strokeWidth / 2}" fill="none" stroke="${color}" stroke-width="${strokeWidth}"/>`;
    } else {
      shape = `<rect x="${cx - r + strokeWidth / 2}" y="${cy - r + strokeWidth / 2}" width="${(r - strokeWidth / 2) * 2}" height="${(r - strokeWidth / 2) * 2}" rx="5" fill="none" stroke="${color}" stroke-width="${strokeWidth}"/>`;
    }
  }

  return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">${shape}</svg>`;
}

function describePiece(id) {
  const tall = (id & 1) !== 0;
  const dark = (id & 2) !== 0;
  const round = (id & 4) !== 0;
  const solid = (id & 8) !== 0;
  return `${tall ? "高" : "低"}${dark ? "濃" : "淡"}${round ? "丸" : "角"}${solid ? "実" : "空"}`;
}

function addLog(text) {
  const li = document.createElement("li");
  li.textContent = text;
  logEl.appendChild(li);
  logEl.scrollTop = logEl.scrollHeight;
}

function cellKey(r, c) {
  return `${r},${c}`;
}

function render(state) {
  currentState = state;
  const winningCells = new Set((state.winning_line || []).map(([r, c]) => cellKey(r, c)));
  const humanTurn = !state.is_over && state.current_player === state.human_player;

  boardEl.innerHTML = "";
  for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 4; c++) {
      const cell = document.createElement("div");
      const pieceId = state.grid[r][c];
      const isEmpty = pieceId === null;
      cell.className = "cell" + (isEmpty ? " empty" : "") + (winningCells.has(cellKey(r, c)) ? " winning" : "");
      if (!isEmpty) {
        cell.innerHTML = pieceSvg(pieceId);
      }
      const placeable = isEmpty && humanTurn && state.phase === "place";
      if (placeable) {
        cell.classList.add("placeable");
        cell.addEventListener("click", () => placePiece(r, c));
      }
      boardEl.appendChild(cell);
    }
  }

  pendingPanel.classList.toggle("hidden", !(humanTurn && state.phase === "place"));
  if (humanTurn && state.phase === "place" && state.pending_piece !== null) {
    pendingPieceEl.innerHTML = pieceSvg(state.pending_piece, { size: 64 });
  }

  selectPanel.classList.toggle("hidden", !(humanTurn && state.phase === "select"));
  if (humanTurn && state.phase === "select") {
    pickerEl.innerHTML = "";
    for (const pid of state.available_pieces) {
      const btn = document.createElement("button");
      btn.className = "piece-btn";
      btn.innerHTML = pieceSvg(pid, { size: 40 });
      btn.title = describePiece(pid);
      btn.addEventListener("click", () => selectPiece(pid));
      pickerEl.appendChild(btn);
    }
  }

  statusEl.classList.remove("win", "error");
  if (state.is_over) {
    if (state.is_draw) {
      statusEl.textContent = "引き分けです";
    } else {
      const winnerIsHuman = state.winner === state.human_player;
      statusEl.textContent = winnerIsHuman ? "あなたの勝ちです!" : "botの勝ちです";
      statusEl.classList.add("win");
    }
  } else if (state.current_player === state.human_player) {
    statusEl.textContent = state.phase === "select" ? "相手(bot)に渡す駒を選んでください" : "駒を置くマスをクリックしてください";
  } else {
    statusEl.textContent = "botが考え中...";
  }
}

function logBotActions(actions) {
  for (const action of actions || []) {
    if (action.type === "select") {
      addLog(`bot: 駒 [${describePiece(action.piece)}] をあなたに渡しました`);
    } else {
      addLog(`bot: (${action.row}, ${action.col}) に配置しました`);
    }
  }
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "unknown error");
  }
  return data;
}

async function newGame() {
  try {
    logEl.innerHTML = "";
    const state = await postJson("/api/new_game", {
      human_first: firstPlayerSelect.value === "human",
      squares_rule: squaresRuleCheckbox.checked,
    });
    render(state);
    logBotActions(state.bot_actions);
    addLog("New Game 開始");
  } catch (err) {
    statusEl.textContent = `エラー: ${err.message}`;
    statusEl.classList.add("error");
  }
}

async function selectPiece(pieceId) {
  try {
    const state = await postJson("/api/select", { piece: pieceId });
    addLog(`あなた: 駒 [${describePiece(pieceId)}] をbotに渡しました`);
    render(state);
    logBotActions(state.bot_actions);
  } catch (err) {
    statusEl.textContent = `エラー: ${err.message}`;
    statusEl.classList.add("error");
  }
}

async function placePiece(row, col) {
  try {
    const state = await postJson("/api/place", { row, col });
    addLog(`あなた: (${row}, ${col}) に配置しました`);
    render(state);
    logBotActions(state.bot_actions);
  } catch (err) {
    statusEl.textContent = `エラー: ${err.message}`;
    statusEl.classList.add("error");
  }
}

async function loadExistingGame() {
  try {
    const res = await fetch("/api/state");
    if (!res.ok) return;
    const state = await res.json();
    render(state);
  } catch (err) {
    // no active game yet; ignore
  }
}

newGameBtn.addEventListener("click", newGame);
loadExistingGame();
