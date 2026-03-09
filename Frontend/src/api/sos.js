import axios from 'axios';
import { API_BASE_URL } from './api';

export const fetchSos = async (tab = "all", location = "", page = 1, limit = 50) => {
    const params = { tab, page, limit };
    if (location) params.place = location;
    
    const response = await axios.get(`${API_BASE_URL}/sos`, { params });
    return response.data;
};
