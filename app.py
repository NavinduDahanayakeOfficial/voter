from flask import Flask,session, request, render_template_string, redirect
import uuid



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
            font-family: Arial;
            max-width: 800px;
            margin: auto;
            padding: 20px;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
        }

        th, td {
            border: 1px solid #ccc;
            padding: 8px;
        }

        th {
            background: #f5f5f5;
        }

        .section {
            margin-top: 25px;
        }
    </style>
</head>
<body>
<p>
    Logged in as:
    <strong>{{ player_name }}</strong>
</p>

<p>
    Host:
    <strong>{{ host }}</strong>
</p>


<h1>Room {{ room_id }}</h1>

<h3>Round {{ round_no }}</h3>

{% if not revealed %}

<div class="section">
    <form method="post" action="/submit/{{ room_id }}">
        <input
            type="text"
            name="guess"
            placeholder="Enter your guess"
            required>

        <button type="submit">
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

    <ul>
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
    <p><strong>{{ correct_answer }}</strong></p>
</div>

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
    <h2>Scoreboard</h2>

    <table>
        <tr>
            <th>Player</th>
            <th>Score</th>
        </tr>

       {% for player, score in scores %}
<tr>
    <td>{{ player }}</td>

   <td>
    {{ "%.1f"|format(score) }}

    <form method="post" action="/change-score/{{ room_id }}" style="display:inline;">
        <input type="hidden" name="player" value="{{ player }}">
        <input type="hidden" name="delta" value="1">
        <button>+1</button>
    </form>

    <form method="post" action="/change-score/{{ room_id }}" style="display:inline;">
        <input type="hidden" name="player" value="{{ player }}">
        <input type="hidden" name="delta" value="0.5">
        <button>+0.5</button>
    </form>

    <form method="post" action="/change-score/{{ room_id }}" style="display:inline;">
        <input type="hidden" name="player" value="{{ player }}">
        <input type="hidden" name="delta" value="-0.5">
        <button>-0.5</button>
    </form>

    {% if is_host %}
    <form method="post" action="/change-score/{{ room_id }}" style="display:inline;">
        <input type="hidden" name="player" value="{{ player }}">
        <input type="hidden" name="delta" value="-1">
        <button>-1</button>
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

</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        player_name = request.form["name"].strip()

        room_id = str(uuid.uuid4())[:6].upper()

        session["player_name"] = player_name

        rooms[room_id] = {
            "answers": [],
            "revealed": False,
            "scores": {},
            "correct_answer": None,
            "round_no": 1,
            "host": player_name
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

    for answer in room["answers"]:

        if (
            answer["guess"].strip().lower()
            ==
            correct_answer.strip().lower()
        ):
           room["scores"][answer["name"]] = round(
    room["scores"][answer["name"]] + 1.0,
    1
)

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