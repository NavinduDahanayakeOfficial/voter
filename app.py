from flask import Flask,session, request, render_template_string, redirect
import uuid

from difflib import SequenceMatcher



app = Flask(__name__)
app.secret_key = "some-random-secret"

rooms = {}


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Guess Game</title>
    <style>
        body {
    font-family: Inter, Arial, sans-serif;
    background: #0f172a;
    color: #f8fafc;
    margin: 0;
    padding: 30px;
}

.container {
    max-width: 900px;
    margin: auto;
}

.card {
    background: #1e293b;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,.25);
}

h1 {
    margin: 0;
    font-size: 2rem;
}

.room-code {
    font-size: 2rem;
    font-weight: bold;
    color: #38bdf8;
}

.host-badge {
    background: #f59e0b;
    color: black;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
}

.player-badge {
    background: #22c55e;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    display: inline-block;
}

input {
    width: 100%;
    padding: 12px;
    margin-top: 10px;
    border-radius: 10px;
    border: none;
    background: #334155;
    color: white;
    box-sizing: border-box;
}

button {
    margin-top: 10px;
    padding: 10px 18px;
    border: none;
    border-radius: 10px;
    cursor: pointer;
    font-weight: bold;
}

.primary {
    background: #3b82f6;
    color: white;
}

.success {
    background: #22c55e;
    color: white;
}

.warning {
    background: #f59e0b;
    color: black;
}

.danger {
    background: #ef4444;
    color: white;
}

.score-btn {
    padding: 5px 10px;
    margin-left: 5px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th {
    background: #334155;
}

th, td {
    padding: 12px;
    text-align: left;
}

tr:nth-child(even) {
    background: rgba(255,255,255,.03);
}

.leader {
    color: #fbbf24;
    font-weight: bold;
    font-size: 1.1rem;
}

.answer-list li {
    padding: 8px;
    margin-bottom: 8px;
    background: #334155;
    border-radius: 8px;
}

.center {
    text-align: center;
}
    </style>
</head>
<body>
<div class="container">


<div class="card center">
    <h1>🎮 Guess The Game</h1>

    <div class="room-code">
        {{ room_id }}
    </div>

    <p>
        Round {{ round_no }}
    </p>

    <p>
        <span class="player-badge">
            {{ player_name }}
        </span>

        {% if is_host %}
        <span class="host-badge">
            HOST
        </span>
        {% endif %}
    </p>
</div>

{% if not revealed %}

<div class="card">
    <h3>Submit Your Guess</h3>

    <form method="post" action="/submit/{{ room_id }}">
        <input
            type="text"
            name="guess"
            placeholder="What game is it?"
            required>

        <button class="primary">
            Submit Guess
        </button>
    </form>
</div>
<p>{{ count }} guesses submitted</p>

<div class="section">
   {% if is_host %}
<form method="post" action="/reveal/{{ room_id }}">
    <button type="submit">Reveal Answers</button>
</form>
{% endif %}
</div>

{% else %}

<div class="section">
    <h2>Submitted Answers</h2>

    <ul class="answer-list">
    {% for answer in answers %}
        <li>
            <strong>{{ answer["name"] }}</strong>
            → {{ answer["guess"] }}
        </li>
    {% endfor %}
    </ul>
</div>

{% if not correct_answer %}

<div class="section">
    <h3>Enter Correct Answer</h3>

    {% if is_host %}
<form method="post" action="/score/{{ room_id }}">
        <input
            type="text"
            name="correct_answer"
            placeholder="Correct Answer"
            required>

        <button type="submit">
            Calculate Scores
        </button>
   </form>
{% endif %}
</div>

{% else %}

<div class="section">
    <h3>Correct Answer:</h3>
    <div class="card center">
    <h2>✅ Correct Answer</h2>
    <h1>{{ correct_answer }}</h1>
</div>
</div>
{% if last_results %}

<div class="section">
    <h2>Round Results</h2>

    <table>
        <tr>
            <th>Player</th>
            <th>Guess</th>
            <th>Points Awarded</th>
        </tr>

        {% for result in last_results %}
        <tr>
            <td>{{ result.player }}</td>
            <td>{{ result.guess }}</td>
            <td>{{ result.points }}</td>
        </tr>
        {% endfor %}
    </table>
</div>

{% endif %}

<div class="section">
   {% if is_host %}
<form method="post" action="/next-round/{{ room_id }}">
        <button type="submit">
            Start Next Round
        </button>
   </form>
{% endif %}
</div>

{% endif %}

{% endif %}

<div class="section">
    <h2>🏆 Leaderboard</h2>

    <table>
        <tr>
            <th>Player</th>
            <th>Score</th>
        </tr>
{% for player, score in scores %}
<tr>

    <td>
        {% if loop.index == 1 %}
            🥇
        {% elif loop.index == 2 %}
            🥈
        {% elif loop.index == 3 %}
            🥉
        {% endif %}

        {{ player }}
    </td>

    <td>
        {{ "%.1f"|format(score) }}
    </td>

    <td>

        {% if is_host %}

        <form method="post" action="/change-score/{{ room_id }}" style="display:inline;">
            <input type="hidden" name="player" value="{{ player }}">
            <input type="hidden" name="delta" value="1">
            <button class="success score-btn">+1</button>
        </form>

        <form method="post" action="/change-score/{{ room_id }}" style="display:inline;">
            <input type="hidden" name="player" value="{{ player }}">
            <input type="hidden" name="delta" value="0.5">
            <button class="primary score-btn">+0.5</button>
        </form>

        <form method="post" action="/change-score/{{ room_id }}" style="display:inline;">
            <input type="hidden" name="player" value="{{ player }}">
            <input type="hidden" name="delta" value="-0.5">
            <button class="warning score-btn">-0.5</button>
        </form>

        <form method="post" action="/change-score/{{ room_id }}" style="display:inline;">
            <input type="hidden" name="player" value="{{ player }}">
            <input type="hidden" name="delta" value="-1">
            <button class="danger score-btn">-1</button>
        </form>

        {% endif %}

    </td>

</tr>
{% endfor %}
    </table>
</div>

{% if is_host %}
<div class="section">
    <form
        method="post"
        action="/reset/{{ room_id }}"
        onsubmit="return confirm('Reset the entire game?');"
    >
        <button type="submit">
            Reset Entire Game
        </button>
    </form>
</div>
{% endif %}
</div>
</body>
</html>
"""
def fuzzy_similarity(a, b):
    return SequenceMatcher(
        None,
        a.lower().strip(),
        b.lower().strip()
    ).ratio()




@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        player_name = request.form["name"].strip()

        if player_name.lower() in ["shallow", "saneth", "san"]:
            player_name += " pop"

        room_id = str(uuid.uuid4())[:6].upper()

        session["player_name"] = player_name

        rooms[room_id] = {
    "answers": [],
    "revealed": False,
    "scores": {},
    "correct_answer": None,
    "round_no": 1,
    "host": player_name,
    "last_results": []
}

        return redirect(f"/room/{room_id}")

    return """
    <h2>Create Game</h2>

    <form method="post">
        <input name="name" placeholder="Your Name" required>
        <button>Create Room</button>
    </form>
    """

@app.route("/room/<room_id>")
def room(room_id):

    if "player_name" not in session:
        return redirect(f"/login/{room_id}")

    room = rooms.get(room_id)



    if not room:
        return "Room not found", 404

    is_host = (
        session.get("player_name")
        ==
        room["host"]
    )

    sorted_scores = sorted(
        room["scores"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    return render_template_string(
        HTML,
        room_id=room_id,
        count=len(room["answers"]),
        answers=room["answers"],
        revealed=room["revealed"],
        scores=sorted_scores,
        correct_answer=room["correct_answer"],
        round_no=room["round_no"],
        is_host=is_host,
        player_name=session["player_name"],
        host=room["host"],
        last_results=room["last_results"],
    )


@app.route("/submit/<room_id>", methods=["POST"])
def submit(room_id):

    room = rooms.get(room_id)

    if not room:
        return "Room not found", 404

    name = session["player_name"]
    guess = request.form["guess"].strip()

    # Prevent duplicate submissions
    for answer in room["answers"]:
        if answer["name"].lower() == name.lower():
            return redirect(f"/room/{room_id}")

    room["answers"].append({
        "name": name,
        "guess": guess
    })

    if name not in room["scores"]:
        room["scores"][name] = 0.0

    return redirect(f"/room/{room_id}")


@app.route("/reveal/<room_id>", methods=["POST"])
def reveal(room_id):

    room = rooms.get(room_id)

    if session.get("player_name") != room["host"]:
        return "Forbidden", 403

    if room:
        room["revealed"] = True

    return redirect(f"/room/{room_id}")


@app.route("/score/<room_id>", methods=["POST"])
def score(room_id):

    room = rooms.get(room_id)

    if session.get("player_name") != room["host"]:
        return "Forbidden", 403

    if not room:
        return "Room not found", 404

    correct_answer = request.form["correct_answer"].strip()

    room["correct_answer"] = correct_answer

    room["last_results"] = []

    for answer in room["answers"]:

        guess = answer["guess"]

        points = 0.0

        # Exact match
        if guess.strip().lower() == correct_answer.strip().lower():
            points = 1.0

        else:

            fuzzy = fuzzy_similarity(
                guess,
                correct_answer
            )

            semantic = semantic_similarity(
                guess,
                correct_answer
            )

            # Strong fuzzy match
            if fuzzy >= 0.85:
                points = 0.5

            # Semantic match
            elif semantic >= 0.80:
                points = 0.75

            elif semantic >= 0.70:
                points = 0.5

            elif semantic >= 0.60:
                points = 0.25

        room["scores"][answer["name"]] = round(
            room["scores"][answer["name"]] + points,
            2
        )
        room["last_results"].append({
        "player": answer["name"],
        "guess": guess,
        "points": points
        })

    return redirect(f"/room/{room_id}")


@app.route("/next-round/<room_id>", methods=["POST"])
def next_round(room_id):

    room = rooms.get(room_id)

    if session.get("player_name") != room["host"]:
        return "Forbidden", 403

    if not room:
        return "Room not found", 404

    room["answers"] = []
    room["revealed"] = False
    room["correct_answer"] = None
    room["round_no"] += 1

    return redirect(f"/room/{room_id}")

@app.route("/change-score/<room_id>", methods=["POST"])
def change_score(room_id):

    room = rooms.get(room_id)

    if session.get("player_name") != room["host"]:
        return "Forbidden", 403

    if not room:
        return "Room not found", 404

    player = request.form["player"]
    delta = float(request.form["delta"])

    if player in room["scores"]:
       room["scores"][player] = round(
    max(0, room["scores"][player] + delta),
    1
) 

    return redirect(f"/room/{room_id}")

@app.route("/reset/<room_id>", methods=["POST"])
def reset(room_id):

    room = rooms.get(room_id)

    if session.get("player_name") != room["host"]:
        return "Forbidden", 403

    if not room:
        return "Room not found", 404

    room["answers"] = []
    room["revealed"] = False
    for player in room["scores"]:
        room["scores"][player] = 0.0
    room["correct_answer"] = None
    room["round_no"] = 1

    return redirect(f"/room/{room_id}")

@app.route("/login/<room_id>", methods=["GET", "POST"])
def login(room_id):

    if request.method == "POST":
        session["player_name"] = request.form["name"]
        return redirect(f"/room/{room_id}")

    return """
    <h2>Enter Name</h2>

    <form method="post">
        <input name="name" required>
        <button>Join</button>
    </form>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)