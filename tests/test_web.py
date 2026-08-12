from quarto.web.app import app


def make_client():
    app.testing = True
    return app.test_client()


def test_new_game_human_first_returns_initial_state():
    client = make_client()
    resp = client.post("/api/new_game", json={"human_first": True})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["phase"] == "select"
    assert data["human_player"] == 0
    assert data["current_player"] == 0
    assert data["bot_actions"] == []
    assert len(data["available_pieces"]) == 16


def test_new_game_bot_first_makes_bot_select_immediately():
    client = make_client()
    resp = client.post("/api/new_game", json={"human_first": False})
    data = resp.get_json()
    assert data["human_player"] == 1
    # bot is player 0 and must act first (select a piece for the human to place)
    assert data["phase"] == "place"
    assert data["current_player"] == 1
    assert data["pending_piece"] is not None
    assert len(data["bot_actions"]) == 1
    assert data["bot_actions"][0]["type"] == "select"


def test_select_then_bot_responds():
    client = make_client()
    client.post("/api/new_game", json={"human_first": True})
    resp = client.post("/api/select", json={"piece": 0})
    assert resp.status_code == 200
    data = resp.get_json()
    # After human selects, bot places and then selects for the human again.
    assert data["phase"] == "place"
    assert data["current_player"] == 0
    assert data["pending_piece"] is not None
    assert len(data["bot_actions"]) == 2


def test_selecting_unavailable_piece_returns_error():
    client = make_client()
    client.post("/api/new_game", json={"human_first": True})
    client.post("/api/select", json={"piece": 0})
    resp = client.post("/api/select", json={"piece": 0})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_acting_out_of_turn_returns_error():
    client = make_client()
    client.post("/api/new_game", json={"human_first": False})
    # It's the bot's turn (player 0); human (player 1) tries to select anyway.
    resp = client.post("/api/select", json={"piece": 3})
    assert resp.status_code == 400


def test_state_without_active_game_returns_404():
    client = make_client()
    client.delete_cookie("session")
    resp = client.get("/api/state")
    assert resp.status_code == 404
