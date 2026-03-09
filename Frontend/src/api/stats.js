import apiClient from './api';

export const fetchStats = async (location = "") => {
    const locParam = location ? `?place=${location}` : "";
    const response = await apiClient.get(`/stats${locParam}`);
    return response.data;
};
