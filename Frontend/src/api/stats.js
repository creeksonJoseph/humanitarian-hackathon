import axios from 'axios';
import { API_BASE_URL } from './api';

export const fetchStats = async (location = "") => {
    const locParam = location ? `?place=${location}` : "";
    const response = await axios.get(`${API_BASE_URL}/stats${locParam}`);
    return response.data;
};
