import apiClient from './api';

export const fetchSos = async (tab = "all", location = "", page = 1, limit = 50) => {
    const params = { tab, page, limit };
    if (location) params.place = location;
    
    const response = await apiClient.get(`/sos`, { params });
    return response.data;
};
