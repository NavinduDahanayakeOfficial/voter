from flask import Flask, request, render_template_string, redirect
import uuid

app = Flask(__name__)

rooms = {}

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Guess Game</title>
</head>
<body>
    <h1>Room {{ room_id }}</h1>

    {% if not revealed %}
    <form method="post" action="/submit/{{ room_id }}">
        <input type="text" name="name" placeholder="Your name" required>
        <input type="text" name="guess" placeholder="Your guess" required>
        <button type="submit">Submit</button>
    </form>

    <p>{{ count }} answers submitted.</p>

    <form method="post" action="/reveal/{{ room_id }}">
        <button type="submit">Reveal Answers</button>
    </form>
    {% else %}
    <h2>Answers</h2>
    <ul>
    {% for answer in answers %}
        <li>{{ answer["name"] }} - {{ answer["guess"] }}</li>
    {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def home():
    room_id = str(uuid.uuid4())[:6]
    rooms[room_id] = {
        "answers": [],
        "revealed": False
    }
    return redirect(f"/room/{room_id}")

@app.route("/room/<room_id>")
def room(room_id):
    room = rooms.get(room_id)

    if not room:
        return "Room not found", 404

    return render_template_string(
        HTML,
        room_id=room_id,
        count=len(room["answers"]),
        answers=room["answers"],
        revealed=room["revealed"]
    )

@app.route("/submit/<room_id>", methods=["POST"])
def submit(room_id):
    room = rooms.get(room_id)

    room["answers"].append({
        "name": request.form["name"],
        "guess": request.form["guess"]
    })

    return redirect(f"/room/{room_id}")

@app.route("/reveal/<room_id>", methods=["POST"])
def reveal(room_id):
    rooms[room_id]["revealed"] = True
    return redirect(f"/room/{room_id}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)