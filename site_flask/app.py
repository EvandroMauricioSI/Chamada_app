from flask import Flask, render_template

# Defina as coordenadas da localização específica
LOCATION_LATITUDE = -22.90624836898053
LOCATION_LONGITUDE = -43.13323656217407

# Crie uma instância do aplicativo
app = Flask(__name__)

# Defina a rota para a página inicial
@app.route('/')
def index():
    return render_template('page1.html')

# Execute o aplicativo
if __name__ == '__main__':
    app.run(debug=True)
