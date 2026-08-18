from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Your integrated Python logic function
def process_slider_value(value):
    # Example logic: just return the squared value for demonstration
    result = int(value) ** 2
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_slider', methods=['POST'])
def update_slider():
    slider_value = request.json['slider_value']
    result = process_slider_value(slider_value)
    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

