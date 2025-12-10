# run.py
from app import create_app
import os

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.context_processor
def utility_processor():
    def current_year():
        from datetime import datetime
        return datetime.now().year
    
    return dict(current_year=current_year)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)