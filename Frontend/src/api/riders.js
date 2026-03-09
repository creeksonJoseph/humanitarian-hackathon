import axios from 'axios';
import { API_BASE_URL } from './api';

export const fetchRiders = async (tab = "all", location = "", search = "", page = 1, limit = 50) => {
    const params = { tab, page, limit };
    if (location) params.place = location;
    if (search) params.search = search;
    
    const response = await axios.get(`${API_BASE_URL}/riders`, { params });
    return response.data;
};

export const verifyRider = async (phone) => {
    const response = await axios.post(`${API_BASE_URL}/riders/${encodeURIComponent(phone)}/verify`);
    return response.data;
};
