import axios from 'axios';
import { API_BASE_URL } from './api';

export const fetchLocations = async () => {
    const response = await axios.get(`${API_BASE_URL}/locations`);
    return response.data;
};
