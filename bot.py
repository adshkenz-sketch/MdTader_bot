import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "MdTader_bot is running successfully!"

# আপনার বটের মূল কোড বা টেলিগ্রাম হ্যান্ডলারগুলো এখানে যোগ করতে পারেন

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
