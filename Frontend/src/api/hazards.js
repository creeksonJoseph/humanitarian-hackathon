import axios from 'axios';
import { API_BASE_URL } from './api';

export const fetchHazards = async (location = "", page = 1, limit = 50) => {
    const params = { page, limit };
    if (location) params.place = location;
    
    const response = await axios.get(`${API_BASE_URL}/hazards`, { params });
    return response.data; 
};

export const clearHazard = async (id) => {
    const response = await axios.post(`${API_BASE_URL}/hazards/${id}/clear`);
    return response.data;
};
