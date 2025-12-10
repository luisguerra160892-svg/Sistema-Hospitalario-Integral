// static/js/mobile-app.js
class MobileApp {
    constructor() {
        this.baseURL = '/api/mobile';
        this.token = localStorage.getItem('auth_token');
    }
    
    async login(username, password) {
        const response = await fetch(`${this.baseURL}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        
        const data = await response.json();
        
        if (data.success) {
            this.token = data.token;
            localStorage.setItem('auth_token', data.token);
            localStorage.setItem('user_data', JSON.stringify(data.user));
        }
        
        return data;
    }
    
    async getCitasHoy() {
        return this.authFetch(`${this.baseURL}/citas/hoy`);
    }
    
    async getPaciente(id) {
        return this.authFetch(`${this.baseURL}/pacientes/${id}`);
    }
    
    async crearConsulta(consultaData) {
        return this.authFetch(`${this.baseURL}/consultas/nueva`, {
            method: 'POST',
            body: JSON.stringify(consultaData)
        });
    }
    
    async authFetch(url, options = {}) {
        if (!this.token) throw new Error('No autenticado');
        
        options.headers = {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        const response = await fetch(url, options);
        return response.json();
    }
}

// Uso en la app móvil
const app = new MobileApp();

// Ejemplo de uso
async function cargarCitasDelDia() {
    try {
        const data = await app.getCitasHoy();
        mostrarCitas(data.citas);
    } catch (error) {
        console.error('Error:', error);
    }
}